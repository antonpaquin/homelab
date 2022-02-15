"""Example Certbot plugins.
For full examples, see `certbot.plugins`.
"""
import io
import time
from typing import Callable, List
import urllib.parse
from xml.etree import ElementTree

import requests
import dns.resolver

from acme import challenges
from certbot import achallenges
from certbot import configuration
from certbot.display import util as display_util
from certbot.plugins import dns_common
import certbot.errors


class NamecheapClient:
    def __init__(self, url: str, client_ip: str, username: str, api_key: str):
        self.url = url
        self.client_ip = client_ip
        self.username = username
        self.api_key = api_key

    def cmd(self, command: str, params: dict = None) -> ElementTree:
        if not params:
            params = {}
        full_params = {
            'ApiUser': self.username,
            'ApiKey': self.api_key,
            'Command': command,
            'ClientIp': self.client_ip,
            'UserName': self.username,
            **params,
        }
        res = requests.post(
            self.url,
            headers={'content-type': 'application/x-www-form-urlencoded'},
            data=urllib.parse.urlencode(full_params)
        )
        res.raise_for_status()
        # try:
        #     res.raise_for_status()
        # except requests.exceptions.HTTPError:
        #     raise certbot.errors.PluginError("Error connecting to NameCheap API")
        buf = io.BytesIO()
        buf.write(res.content)
        buf.seek(0)
        xml = ElementTree.parse(buf)
        # if xml.getroot().attrib['Status'] != 'OK':
        #     # Anton: apologies if you're debugging here.
        #     # I could have generated a proper message but pulling apart XML is friggin annoying
        #     raise certbot.errors.PluginError("Namecheap API Error")
        return xml


def await_propagation(domain: str, validation: str, timescale: int = 5) -> None:
    while True:
        try:
            q = dns.resolver.resolve(domain, 'TXT')
        except dns.resolver.NoAnswer:
            display_util.notify("DNS no TXT response")
            time.sleep(timescale)
            continue
        resp = q[0].to_text().strip('"')
        if resp == validation:
            return
        display_util.notify(f"{domain}: {resp} != {validation}, continuing to wait")
        time.sleep(timescale)


def _merge_hosts(sld: str, tld: str, etree: ElementTree, nhosts: List[dict]) -> dict:
    root = etree.getroot()
    command_response = [elem for elem in root if elem.tag.endswith("CommandResponse")][0]
    dghr = [elem for elem in command_response if elem.tag.endswith("DomainDNSGetHostsResult")][0]
    res = {
        "SLD": sld,
        "TLD": tld,
        "EmailType": dghr.attrib["EmailType"],
    }
    hosts = []
    for host in dghr:
        hosts.append({
            "HostName": host.attrib["Name"],
            "RecordType": host.attrib["Type"],
            "Address": host.attrib["Address"],
            "MXPref": host.attrib["MXPref"],
            "TTL": host.attrib["TTL"],
        })
    for nhost in nhosts:
        nrecord = {
            "HostName": nhost["HostName"],
            "RecordType": nhost["RecordType"],
            "Address": nhost["Address"],
            "MXPref": nhost["MXPref"],
            "TTL": nhost["TTL"],
        }
        for idx, host in hosts:
            if host["HostName"] == nrecord["HostName"] and host["RecordType"] == nrecord["RecordType"]:
                hosts[idx] = nrecord
                break
        else:
            hosts.append(nrecord)
    for idx, host in enumerate(sorted(hosts, key=lambda x: x["HostName"])):
        n = idx + 1
        res[f"HostName{n}"] = host["HostName"]
        res[f"RecordType{n}"] = host["RecordType"]
        res[f"Address{n}"] = host["Address"]
        res[f"MXPref{n}"] = host["MXPref"]
        res[f"TTL{n}"] = host["TTL"]
    return res


class Authenticator(dns_common.DNSAuthenticator):
    """Example Authenticator."""

    description = "Namecheap Authenticator plugin"

    def __init__(self, config: configuration.NamespaceConfig, name: str) -> None:
        super().__init__(config, name)

    @classmethod
    def add_parser_arguments(cls, add: Callable[..., None]) -> None:
        """Add plugin arguments to the CLI argument parser.

        :param callable add: Function that proxies calls to
            `argparse.ArgumentParser.add_argument` prepending options
            with unique plugin name prefix.

        """
        super().add_parser_arguments(add)
        add("public-ip", help="IP Address of this connection (must be on Namecheap whitelist)")
        add("api-key", help="Namecheap API key")
        add("api-user", help="Namecheap Username")
        add("namecheap-api-url", default='https://api.namecheap.com/xml.response', help="Namecheap URL (Swap out for sandbox API)")

    def more_info(self) -> str:
        return "Namecheap Authenticator more_info"

    def perform(
        self,
        achalls: List[achallenges.AnnotatedChallenge]
    ) -> List[challenges.ChallengeResponse]:

        nc_client = NamecheapClient(
            url=self.conf('namecheap-api-url'),
            client_ip=self.conf('public-ip'),
            username=self.conf('api-user'),
            api_key=self.conf('api-key'),
        )

        nc_client.cmd("namecheap.users.getBalances")  # Check: credentials are OK?

        self._attempt_cleanup = True

        domains = {}
        responses = []
        for achall in achalls:
            domain = achall.domain
            validation_domain_name = achall.validation_domain_name(domain)
            validation = achall.validation(achall.account_key)

            if domain not in domains:
                domains[domain] = []
            domains[domain].append((validation_domain_name, validation))

            responses.append(achall.response(achall.account_key))

        for domain, validation_info in domains.items():
            sld, tld = domain.split('.', 1)
            hosts = nc_client.cmd('namecheap.domains.dns.getHosts', {"SLD": sld, "TLD": tld})
            nhost_entries = []
            for validation_domain_name, validation in validation_info:
                assert validation_domain_name.endswith(domain)
                nhost_entries.append({
                    "HostName": validation_domain_name[:-(len(domain) + 1)],
                    "RecordType": "TXT",
                    "Address": validation,
                    "MXPref": "",
                    "TTL": 60,
                })
            new_hosts = _merge_hosts(sld, tld, hosts, nhost_entries)
            nc_client.cmd("namecheap.domains.dns.setHosts", new_hosts)

        for domain, validation_info in domains.items():
            for validation_domain_name, validation in validation_info:
                display_util.notify("Waiting a while for DNS changes to propagate for %s" % validation_domain_name)
                await_propagation(validation_domain_name, validation)

        # DNS updates take time to propagate and checking to see if the update has occurred is not
        # reliable (the machine this code is running on might be able to see an update before
        # the ACME server). So: we sleep for a short amount of time we believe to be long enough.
        display_util.notify("Waiting extra %d seconds to confirm DNS changes have propagated" % self.conf('propagation-seconds'))
        time.sleep(self.conf('propagation-seconds'))

        return responses

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        pass  # obsoleted

    def _setup_credentials(self) -> None:  # pragma: no cover
        pass  # obsoleted

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:  # pragma: no cover
        """
        Deletes the DNS TXT record which would have been created by `_perform_achall`.
        Fails gracefully if no such record exists.
        :param str domain: The domain being validated.
        :param str validation_domain_name: The validation record domain name.
        :param str validation: The validation record content.
        """
        pass  # Lazy
