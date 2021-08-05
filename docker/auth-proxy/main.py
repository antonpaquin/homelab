#! /usr/bin/env python3

import argparse
import base64
import cryptography.fernet
import datetime
import json
import logging
import os
import urllib.parse
import uuid
from typing import List, Set, Optional

import flask
import jwt
import requests

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class AuthError(Exception): pass


class OIDCMeta:
    raw: dict
    authorization_endpoint: str
    userinfo_endpoint: str
    token_endpoint: str
    jwks_uri: str
    id_token_algorithms: List[str]

    def __init__(self, raw: dict):
        self.raw = raw
        self.authorization_endpoint = raw["authorization_endpoint"]
        self.userinfo_endpoint = raw["userinfo_endpoint"]
        self.token_endpoint = raw["token_endpoint"]
        self.jwks_uri = raw["jwks_uri"]
        self.id_token_algorithms = raw["id_token_signing_alg_values_supported"]

    @classmethod
    def from_issuer(cls, issuer_url: str) -> 'OIDCMeta':
        if not issuer_url.endswith('/'):
            issuer_url = issuer_url + '/'
        r = requests.get(issuer_url + '.well-known/openid-configuration')
        r.raise_for_status()
        return cls(json.loads(r.content))


class AuthRequest:
    def __init__(self):
        pass

    @classmethod
    def from_dict(cls, d: dict) -> 'AuthRequest':
        return AuthRequest()


class DomainConfig:
    role: str
    domain: str
    auth_request: AuthRequest

    def __init__(self, role: str, domain: str, auth_request: AuthRequest):
        self.role = role
        self.domain = domain
        self.auth_request = auth_request

    @classmethod
    def from_dict(cls, d: dict) -> 'DomainConfig':
        return DomainConfig(
            role=d["role"],
            domain=d["domain"],
            auth_request=AuthRequest.from_dict(d["auth_request"]),
        )


class Config:
    oidc_meta: OIDCMeta
    redirect_uri: str
    client_id: str
    client_secret: str
    protected_domains: List[DomainConfig]

    def __init__(self, issuer_url: str, redirect_uri: str, client_id: str, client_secret: str, protected_domains: List[DomainConfig]):
        self.oidc_meta = OIDCMeta.from_issuer(issuer_url)
        self.redirect_uri = redirect_uri
        self.client_id = client_id
        self.client_secret = client_secret
        self.protected_domains = protected_domains

    @classmethod
    def from_dict(cls, d: dict) -> 'Config':
        return Config(
            issuer_url=d["issuer_url"],
            redirect_uri=d["redirect_uri"],
            client_id=d["client_id"],
            client_secret=d["client_secret"],
            protected_domains=[DomainConfig.from_dict(dc) for dc in d["protected_domains"]],
        )

    @classmethod
    def from_file(cls, fpath: str) -> 'Config':
        with open(fpath, 'r') as in_f:
            data = json.load(in_f)
        return cls.from_dict(data)


class AuthenticationToken:
    _timeout = 300

    user: str
    role: str

    def __init__(self, user: str):
        self.user = user

    @staticmethod
    def build(fernet: cryptography.fernet.Fernet, user: str, role: str) -> str:
        data = json.dumps({
            "user": user,
            "role": role,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        return fernet.encrypt(data.encode('ascii')).decode('ascii')

    @staticmethod
    def parse(fernet: cryptography.fernet.Fernet, token: str) -> 'AuthenticationToken':
        try:
            data = json.loads(fernet.decrypt(token.encode('ascii')).decode('ascii'))
        except cryptography.fernet.InvalidToken:
            raise AuthError()
        auth_dt = datetime.datetime.fromisoformat(data["timestamp"])
        if (datetime.datetime.now() - auth_dt) > datetime.timedelta(seconds=AuthenticationToken._timeout):
            raise AuthError()
        return AuthenticationToken(user=data["user"])


class ValidationToken:
    user: str

    def __init__(self, user: str):
        self.user = user

    @staticmethod
    def build(fernet: cryptography.fernet.Fernet, user: str) -> str:
        data = json.dumps({
            "user": user,
        })
        return 'Bearer ' + fernet.encrypt(data.encode('ascii')).decode('ascii')

    @staticmethod
    def parse(fernet: cryptography.fernet.Fernet, token: str) -> 'ValidationToken':
        if not token.startswith('Bearer '):
            raise AuthError()
        tkn = token[7:]
        try:
            data = json.loads(fernet.decrypt(tkn.encode('ascii')).decode('ascii'))
        except cryptography.fernet.InvalidToken:
            raise AuthError()
        return ValidationToken(user=data["user"])


class OIDCProxy:
    # Best docs I've found for this at https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc
    config: Config

    def __init__(self, config: Config):
        self.config = config

        self.jwks = jwt.PyJWKClient(self.config.oidc_meta.jwks_uri)
        self.fernet = cryptography.fernet.Fernet(cryptography.fernet.Fernet.generate_key())

        self.app = flask.Flask(__name__)
        self.app.route('/validate', methods=["GET"])(self.validate)
        self.app.route("/login", methods=["GET"])(self.login)
        self.app.route("/auth", methods=["POST"])(self.auth)
        self.app.route('/', defaults={'path': ''})(self.root)
        self.app.route('/<path:path>')(self.root)

    def validate(self) -> flask.Response:
        validation_cookie = "X-Authproxy-Authorization"
        request = flask.request

        if validation_cookie in request.cookies:
            try:
                token = ValidationToken.parse(self.fernet, request.cookies.get(validation_cookie))
                return flask.Response('', 200)
            except AuthError:
                pass

        target_url = request.headers.get("X-Original-Url")
        if not target_url:
            return flask.Response('', 401)

        url = urllib.parse.urlparse(target_url)
        query = urllib.parse.parse_qs(url.query)

        if '_AuthProxyToken' in query:
            maybe_token = query["_AuthProxyToken"][0]
        else:
            return flask.Response('', 401)

        try:
            auth_info = AuthenticationToken.parse(self.fernet, maybe_token)
        except AuthError:
            return flask.Response('', 401)

        resp = flask.Response('', 200)
        resp.set_cookie(validation_cookie, ValidationToken.build(self.fernet, auth_info.user))
        return resp

    def login(self) -> flask.Response:
        args = flask.request.args
        rd = args["rd"]

        authorization_url = self.config.oidc_meta.authorization_endpoint
        state = {"rd": rd}
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": "openid roles",
            "nonce": self.gen_nonce(),
            "response_mode": "form_post",
            "state": base64.b64encode(json.dumps(state).encode('ascii')),
        }
        target_dest = authorization_url + '?' + urllib.parse.urlencode(params)
        return flask.redirect(target_dest)

    def auth(self) -> flask.Response:
        request = flask.request
        form = request.form

        if "state" in form and "code" in form:
            maybe_state = form["state"]
            maybe_code = form["code"]
        else:
            return self.auth_failed("Invalid login request")

        params = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": self.config.redirect_uri,
            "code": maybe_code,
        }
        r = requests.post(self.config.oidc_meta.token_endpoint, data=params)

        if r.status_code != 200:
            return self.auth_failed("Token request not happy")

        try:
            data = r.json()
        except json.JSONDecodeError:
            return self.auth_failed("Token request is very confused")

        if "id_token" in data:
            maybe_id_token = data["id_token"]
        else:
            return self.auth_failed("Token request is somewhat confused")

        try:
            jwk = self.jwks.get_signing_key_from_jwt(maybe_id_token)
            id_token = jwt.decode(
                jwt=maybe_id_token,
                key=jwk.key,
                algorithms=self.config.oidc_meta.id_token_algorithms,
                audience=self.config.client_id,
            )
        except jwt.exceptions.PyJWTError as e:
            logger.info(e)
            return self.auth_failed("Token is being sneaky")

        state = json.loads(base64.b64decode(maybe_state))
        rd = state["rd"]

        roles = set(id_token["resource_access"]["roles"])
        target = urllib.parse.urlparse(rd).netloc
        domain = self.match_domain(target, roles)
        if not domain:
            return self.auth_failed("No matching role")

        return self.auth_success(id_token["name"], rd, domain)

    def match_domain(self, target: str, roles: Set[str]) -> Optional[DomainConfig]:
        for candidate_domain in self.config.protected_domains:
            if candidate_domain.domain == target and candidate_domain.role in roles:
                return candidate_domain
        return None

    def auth_failed(self, msg: str) -> flask.Response:
        return flask.Response(msg, 401)

    def auth_success(self, user: str, rd: str, domain: DomainConfig) -> flask.Response:
        url = urllib.parse.urlparse(rd)
        query = urllib.parse.parse_qsl(url.query)
        query.append(("_AuthProxyToken", AuthenticationToken.build(self.fernet, user, domain.role)))
        mod_query = urllib.parse.urlencode(query)
        mod_rd = urllib.parse.urlunparse((url.scheme, url.netloc, url.path, url.params, mod_query, url.fragment))
        resp = flask.redirect(mod_rd)
        return resp

    def root(self, path) -> flask.Response:
        request = flask.request
        resp = json.dumps({
            'url': request.url,
            'path': path,
            'headers': dict(request.headers),
            'args': request.args,
            'form': request.form,
            'data': request.data.decode('utf-8'),
            'method': request.method,
        })
        logger.info(resp)
        return flask.Response(resp, 200)

    @staticmethod
    def gen_nonce() -> str:
        return str(uuid.uuid4())  # apparently this is good enough


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config')
    parser.add_argument('--host', default=os.environ.get("APP_HOST", '127.0.0.1'))
    parser.add_argument('--port', type=int, default=int(os.environ.get("APP_PORT", '8000')))
    return parser.parse_args()


if __name__ == '__main__':
    args = cli()
    cfg = Config.from_file(args.config)
    server = OIDCProxy(cfg)
    server.app.run(args.host, args.port)
else:
    config_fpath = os.environ["AUTH_PROXY_CONFIG"]
    cfg = Config.from_file(config_fpath)
    server = OIDCProxy(cfg)
    app = server.app
