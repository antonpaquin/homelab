#! /usr/bin/env python3

import argparse
import base64
import copy
import cryptography.fernet
import datetime
import functools
import json
import logging
import os
import random
import sqlite3
import urllib.parse
import uuid
import textwrap
import traceback
from typing import List, Optional, Dict, Tuple, Iterable, Callable, Set, Union

import flask
import jwt
import requests

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class AuthError(Exception):
    message: str

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthMethod:
    type: str

    def __init__(self):
        pass

    def authenticate(self, rd: str, validation_token: str) -> flask.Response:
        raise NotImplementedError('stub!')

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> 'AuthMethod':
        if not d:
            return AuthNull.from_dict(d)
        if d["type"] == "request":
            return AuthRequest.from_dict(d)
        elif d["type"] == "passthrough":
            return AuthPassthrough.from_dict(d)
        return AuthNull.from_dict(d)


class AuthNull(AuthMethod):
    def authenticate(self, rd: str, validation_token: str) -> flask.Response:
        return flask.redirect(rd)

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> 'AuthNull':
        return AuthNull()


class _AuthRequestSend:
    method: str
    url: str
    headers: dict
    body: str

    def __init__(self, method: str, url: str, headers: dict, body: str):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body

    @classmethod
    def from_dict(cls, d: dict) -> '_AuthRequestSend':
        return cls(method=d.get("method", "GET"), url=d["url"], headers=d.get("headers", {}), body=d.get("body", ""))


class _AuthRequestRecv:
    set_cookie: bool
    client_script: Optional[str]

    def __init__(self, set_cookie: bool, client_script: Optional[str]):
        self.set_cookie = set_cookie
        self.client_script = client_script

    @classmethod
    def from_dict(cls, d: dict) -> '_AuthRequestRecv':
        return cls(set_cookie=d.get("set-cookie", True), client_script=d.get("client-script", None))


class AuthRequest(AuthMethod):
    request: _AuthRequestSend
    response: _AuthRequestRecv

    def __init__(self, request: _AuthRequestSend, response: _AuthRequestRecv):
        super().__init__()
        self.request = request
        self.response = response

    def authenticate(self, rd: str, validation_token: str) -> flask.Response:
        logger.info(f"Starting request to {self.request.url}")
        headers = copy.deepcopy(self.request.headers)
        r = requests.request(
            self.request.method,
            self.request.url,
            headers=headers,
            cookies={OIDCProxy.VALIDATION_COOKIE: validation_token},
            data=self.request.body,
        )
        logger.info(f"Completed request to {self.request.url}: {r.status_code}")
        logger.info(f"Text: {r.text}")

        if not (200 <= r.status_code < 300):
            raise AuthError("Configured login request failed")

        if self.response.client_script is None:
            resp = flask.redirect(rd)
        else:
            req = {
                'headers': dict(r.headers),
                'body': r.text,
                'status_code': r.status_code,
            }
            req_jsn_b64 = base64.b64encode(json.dumps(req).encode('utf-8')).decode('ascii')
            body = textwrap.dedent('''
                <html>
                <body>
                    <script>
                    const response = JSON.parse(atob("{req_jsn_b64}"));
                    const authproxy_rd = "{rd}";
                    const authproxy_validation_token = "{validation_token}";
                    {client_script}
                    </script>
                </body>
                </html>
            ''').format(
                req_jsn_b64=req_jsn_b64,
                client_script=self.response.client_script,
                rd=rd,
                validation_token=validation_token,
            )
            resp = flask.Response(body)

        if self.response.set_cookie:
            for k, v in r.cookies.items():
                resp.set_cookie(k, v)

        return resp

    @classmethod
    def from_dict(cls, d: dict) -> 'AuthRequest':
        return AuthRequest(
            request=_AuthRequestSend.from_dict(d["request"]),
            response=_AuthRequestRecv.from_dict(d["response"]),
        )


class AuthPassthrough(AuthMethod):
    url: str
    script_snippet: Optional[str]

    def __init__(self, url: str, script_snippet: Optional[str]):
        super().__init__()
        self.url = url
        self.script_snippet = script_snippet

    def authenticate(self, resp: flask.Response, validation_token: str) -> flask.Response:
        r = requests.get(self.url, cookies={OIDCProxy.VALIDATION_COOKIE: validation_token})
        body = r.text
        body = body + textwrap.dedent('''
            <script>
            {script_snippet}
            </script>
        ''').format(script_snippet=self.script_snippet)
        headers = r.headers
        headers.pop("Content-Encoding")
        resp = flask.Response(
            body,
            r.status_code,
            dict(headers),
        )
        return resp

    @classmethod
    def from_dict(cls, d: dict) -> 'AuthPassthrough':
        return AuthPassthrough(
            url=d["url"],
            script_snippet=d.get("script-snippet"),
        )


class DomainConfig:
    role: str
    domain: str
    auth: AuthMethod

    def __init__(self, role: str, domain: str, auth: AuthMethod):
        self.role = role
        self.domain = domain
        self.auth = auth

    @classmethod
    def from_dict(cls, d: dict) -> 'DomainConfig':
        return DomainConfig(
            role=d["role"],
            domain=d["domain"],
            auth=AuthMethod.from_dict(d["auth"]),
        )


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


class Config:
    oidc_meta: OIDCMeta
    redirect_uri: str
    client_id: str
    client_secret: str
    protected_domains: List[DomainConfig]
    authproxy_endpoint: str
    key_seed: str
    db_path: str

    def __init__(
            self,
            issuer_url: str,
            redirect_uri: str,
            client_id: str,
            client_secret: str,
            protected_domains: List[DomainConfig],
            authproxy_endpoint: str,
            key_seed: str,
            db_path: str,
    ):
        self.oidc_meta = OIDCMeta.from_issuer(issuer_url)
        self.redirect_uri = redirect_uri
        self.client_id = client_id
        self.client_secret = client_secret
        self.protected_domains = protected_domains
        self.authproxy_endpoint = authproxy_endpoint
        self.key_seed = key_seed
        self.db_path = db_path

    @classmethod
    def from_dict(cls, d: dict) -> 'Config':
        return Config(
            issuer_url=d["issuer_url"],
            redirect_uri=d["redirect_uri"],
            client_id=d["client_id"],
            client_secret=d["client_secret"],
            protected_domains=[DomainConfig.from_dict(dc) for dc in d["protected_domains"]],
            authproxy_endpoint=d["authproxy_endpoint"],
            key_seed=d["key_seed"],
            db_path=d["db_path"],
        )

    @classmethod
    def from_file(cls, fpath: str) -> 'Config':
        with open(fpath, 'r') as in_f:
            data = json.load(in_f)
        return cls.from_dict(data)


class OauthState:
    rd: str
    timestamp: datetime.datetime
    _ttl = 300

    def __init__(self, rd: str, timestamp: datetime.datetime):
        self.rd = rd
        self.timestamp = timestamp

    @staticmethod
    def new(rd: str) -> str:
        state = {"rd": rd, "timestamp": int(datetime.datetime.now().timestamp()), "nonce": str(uuid.uuid4())}
        return base64.b64encode(json.dumps(state).encode('ascii')).decode('ascii')

    @staticmethod
    def parse(s: str) -> 'OauthState':
        data = json.loads(base64.b64decode(s.encode('ascii')).decode('ascii'))
        ts = datetime.datetime.fromtimestamp(data["timestamp"])
        if (datetime.datetime.now() - ts) > datetime.timedelta(seconds=OauthState._ttl):
            raise AuthError("State is expired, try again")
        return OauthState(
            rd=data["rd"],
            timestamp=ts,
        )


class KeycloakIdToken:
    name: str
    roles: List[str]

    def __init__(self, name: str, roles: List[str]):
        self.name = name
        self.roles = roles

    @classmethod
    def from_dict(cls, d: dict) -> 'KeycloakIdToken':
        if "resource_access" not in d:
            raise AuthError("ID provider did not send \"resource_access\"")
        if "roles" not in d["resource_access"]:
            raise AuthError("ID provider did not send \"resource_access.roles\"")
        return cls(name=d["preferred_username"], roles=d["resource_access"]["roles"])

    @classmethod
    def from_jwt(cls, config: Config, jwks: jwt.PyJWKClient, token: str):
        try:
            jwk = jwks.get_signing_key_from_jwt(token)
            id_token = jwt.decode(
                jwt=token,
                key=jwk.key,
                algorithms=config.oidc_meta.id_token_algorithms,
                audience=config.client_id,
            )
        except jwt.exceptions.PyJWTError as e:
            raise AuthError("JWT is invalid")

        return cls.from_dict(id_token)


class LoginToken:
    _timeout = 300

    user: str
    role: str
    domain: str

    def __init__(self, user: str, role: str, domain: str):
        self.user = user
        self.role = role
        self.domain = domain

    @staticmethod
    def new(fernet: cryptography.fernet.Fernet, user: str, role: str, domain: str) -> str:
        data = json.dumps({
            "user": user,
            "role": role,
            "domain": domain,
            "timestamp": int(datetime.datetime.now().timestamp()),
        })
        return fernet.encrypt(data.encode('ascii')).decode('ascii')

    @staticmethod
    def parse(fernet: cryptography.fernet.Fernet, token: str) -> 'LoginToken':
        try:
            data = json.loads(fernet.decrypt(token.encode('ascii')).decode('ascii'))
        except cryptography.fernet.InvalidToken:
            raise AuthError("Login Token is invalid")
        auth_dt = datetime.datetime.fromtimestamp(data["timestamp"])
        if (datetime.datetime.now() - auth_dt) > datetime.timedelta(seconds=LoginToken._timeout):
            raise AuthError("Login Token is expired, try again")
        return LoginToken(user=data["user"], role=data["role"], domain=data["domain"])


class ValidationToken:
    user: str

    def __init__(self, user: str):
        self.user = user

    @staticmethod
    def new(fernet: cryptography.fernet.Fernet, user: str) -> str:
        data = json.dumps({
            "user": user,
        })
        return 'Bearer ' + fernet.encrypt(data.encode('ascii')).decode('ascii')

    @staticmethod
    def parse(fernet: cryptography.fernet.Fernet, token: str) -> 'ValidationToken':
        if not token.startswith('Bearer '):
            raise AuthError("Validation token invalid format")
        tkn = token[7:]
        try:
            data = json.loads(fernet.decrypt(tkn.encode('ascii')).decode('ascii'))
        except cryptography.fernet.InvalidToken:
            raise AuthError("Validation token is invalid")
        return ValidationToken(user=data["user"])


class OIDCProxy:
    # Best docs I've found for this at https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc
    config: Config
    VALIDATION_COOKIE = 'X-Authproxy-Authorization'
    USER_HEADER = 'X-Authproxy-User'

    def __init__(self, config: Config):
        self.config = config

        self.jwks = jwt.PyJWKClient(self.config.oidc_meta.jwks_uri)
        self.fernet = deterministic_fernet(config.key_seed)

        self.conn = self._init_db(self.config.db_path)

        self._login_success_endpoint = config.authproxy_endpoint + "/login_success"
        self._static_endpoint = config.authproxy_endpoint + "/static"

        self.app = flask.Flask(__name__)
        self.app.route('/validate', methods=["GET"])(self.validate)
        self.app.route("/login", methods=["GET"])(self.login)
        self.app.route("/auth", methods=["POST"])(self.auth)
        self.app.route(self._static_endpoint + "/<path:path>", methods=["GET"])(self.authproxy_static)
        self.app.route(self._login_success_endpoint, methods=["GET"])(self.login_success)
        self.app.route('/', defaults={'path': ''})(self.root)
        self.app.route('/<path:path>')(self.root)

        self.app.before_request(self.log_request)
        self.app.errorhandler(AuthError)(self.auth_failed)

    @staticmethod
    def _init_db(db_path: str) -> sqlite3.Connection:
        if os.path.exists(db_path):
            return sqlite3.connect(db_path)
        conn = sqlite3.connect(db_path)
        cur: sqlite3.Cursor = conn.cursor()
        cur.execute("CREATE TABLE session_state (session TEXT, state TEXT)")
        cur.execute("CREATE INDEX session_idx ON session_state (session)")
        conn.commit()
        return conn

    def set_session_state(self, session_key: str, state: str):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO session_state (session, state) VALUES (?, ?)", (session_key, state))
        self.conn.commit()

    def get_session_state(self, session_key: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT state FROM session_state WHERE session = ?", (session_key,))
        row = cur.fetchone()
        if not row:
            return None
        return row[0]

    def log_request(self):
        logger.info(json.dumps({
            "path": flask.request.path,
            "args": flask.request.args,
            "form": flask.request.form,
            "headers": dict(flask.request.headers),
            "url": flask.request.url,
            "data": flask.request.data.decode('utf-8'),
        }, indent=4))

    def validate(self) -> flask.Response:
        request = flask.request

        _url = request.headers.get("X-Original-Url")
        if not _url:
            return flask.Response('', 401)

        url = urllib.parse.urlparse(_url)
        if url.path == self._login_success_endpoint:
            return flask.Response('', 200)

        if self.VALIDATION_COOKIE in request.cookies:
            try:
                token = self._load_validation_token(request.cookies.get(self.VALIDATION_COOKIE))
                return flask.Response('', 200, headers={self.USER_HEADER: token.user})
            except AuthError as e:
                pass

        return flask.Response('', 401)

    @functools.lru_cache(maxsize=200)
    def _load_validation_token(self, token: str) -> ValidationToken:
        return ValidationToken.parse(self.fernet, token)

    def login(self) -> flask.Response:
        args = flask.request.args
        session_key = str(uuid.uuid4())
        resp, state = _authstep_0_login(self.config, args["rd"])
        resp.set_cookie('session', session_key)
        self.set_session_state(session_key, state)
        return resp

    def auth(self) -> flask.Response:
        session_key = flask.request.cookies.get("session")
        check_state = self.get_session_state(session_key)
        if not check_state:
            raise AuthError("User session has no associated state")

        oauth_code, state = _authstep_1_check_form(self.config, flask.request.form, check_state)
        id_token = _authstep_2_get_token(self.config, self.jwks, oauth_code)
        authorized_domain = _authstep_3_authorization(self.config, id_token, state)

        return self.auth_success(id_token.name, state.rd, authorized_domain)

    def authproxy_static(self, path: str) -> flask.Response:
        if path == "authfail_img":
            fchoices = os.listdir("authfail_img")
            fname = os.path.join("authfail_img", random.choice(fchoices))
            with open(fname, 'rb') as in_f:
                fdata = in_f.read()
            return flask.Response(fdata)
        return flask.Response('', 404)

    def auth_failed(self, err: AuthError) -> flask.Response:
        return flask.Response(textwrap.dedent(f'''
            <img src="{self._static_endpoint}/authfail_img" style="max-width: 90vw; max-height: 90vh;"/>
            <h3>{err.message}</h3>
        '''), 401)

    def auth_success(self, user: str, rd: str, domain: DomainConfig) -> flask.Response:
        url = urllib.parse.urlparse(rd)
        query = [
            ("AuthProxyToken", LoginToken.new(self.fernet, user, domain.role, domain.domain)),
            ("rd", rd),
        ]
        mod_query = urllib.parse.urlencode(query)
        mod_rd = urllib.parse.urlunparse((url.scheme, url.netloc, self._login_success_endpoint, None, mod_query, None))
        resp = flask.redirect(mod_rd)
        return resp

    def login_success(self) -> flask.Response:
        login_token = LoginToken.parse(self.fernet, flask.request.args["AuthProxyToken"])

        # Guaranteed to be at least one, or else the login should have failed
        domain_config: DomainConfig = pick_domain(self.config.protected_domains, login_token.domain, login_token.role)
        validation_token: str = ValidationToken.new(self.fernet, login_token.user)

        resp = domain_config.auth.authenticate(flask.request.args["rd"], validation_token)
        resp.set_cookie(self.VALIDATION_COOKIE, validation_token)

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


def _authstep_0_login(config: Config, rd: str) -> Tuple[flask.Response, str]:
    state = OauthState.new(rd)
    authorization_url = config.oidc_meta.authorization_endpoint
    params = {
        "client_id": config.client_id,
        "response_type": "code",
        "redirect_uri": config.redirect_uri,
        "scope": "openid roles",
        "nonce": _gen_nonce(),
        "response_mode": "form_post",
        "state": state,
    }
    target_dest = authorization_url + '?' + urllib.parse.urlencode(params)
    resp = flask.redirect(target_dest)
    return resp, state


def _authstep_1_check_form(config: Config, form: dict, check_state: str) -> Tuple[str, OauthState]:
    if "state" not in form:
        raise AuthError("Missing OAuth State")
    if "code" not in form:
        raise AuthError("Missing OAuth Code")
    if form["state"] != check_state:
        raise AuthError("OAuth State Mismatch, something suspicious is going on")

    state = OauthState.parse(form["state"])
    return form["code"], state


def _authstep_2_get_token(config: Config, jwks: jwt.PyJWKClient, code: str) -> KeycloakIdToken:
    params = {
        "grant_type": "authorization_code",
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "redirect_uri": config.redirect_uri,
        "code": code,
    }
    r = requests.post(config.oidc_meta.token_endpoint, data=params)

    if r.status_code != 200:
        raise AuthError("ID Provider rejected client")

    try:
        data = r.json()
    except json.JSONDecodeError:
        raise AuthError("ID Provider invalid response")

    if "id_token" in data:
        maybe_id_token = data["id_token"]
    else:
        raise AuthError("ID Provider did not send id token. Is it configured?")

    return KeycloakIdToken.from_jwt(config, jwks, maybe_id_token)


def _authstep_3_authorization(config: Config, id_token: KeycloakIdToken, state: OauthState) -> DomainConfig:
    roles = set(id_token.roles)
    target = urllib.parse.urlparse(state.rd).netloc
    domain = pick_domain(config.protected_domains, target, roles)
    if domain is None:
        raise AuthError(f"User \"{id_token.name}\" is not authorized to access \"{target}\"")
    return domain


def _gen_nonce() -> str:
    return str(uuid.uuid4())  # apparently this is good enough


def deterministic_fernet(key_seed: str) -> cryptography.fernet.Fernet:
    return cryptography.fernet.Fernet(base64.b64encode(random.Random(key_seed).randbytes(32)))


def pick_domain(domains: List[DomainConfig], target: str, accepted_roles: Union[Set[str], str]) -> Optional[DomainConfig]:
    if isinstance(accepted_roles, set):
        pred = lambda domain_config: target == domain_config.domain and domain_config.role in accepted_roles
    else:
        pred = lambda domain_config: target == domain_config.domain and domain_config.role == accepted_roles
    return first(pred, domains)


def first(pred: Callable, itr: Iterable):
    for k in itr:
        if pred(k):
            return k


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
