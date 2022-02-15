import functools
import json
import os
from typing import Tuple

import kubernetes.client
import kubernetes.config

kubernetes.config.load_incluster_config()


def get_certificates_path(domain: str) -> Tuple[str, str]:
    # What happens when it"s not wildcard? *shrug*
    domain_l, domain_r = domain.split(".", 1)
    return (
        f"/etc/letsencrypt/live/{domain_r}/fullchain.pem",
        f"/etc/letsencrypt/live/{domain_r}/privkey.pem"
    )


def does_secret_exist(client: kubernetes.client.CoreV1Api, name: str, namespace: str) -> bool:
    secret_list = client.list_namespaced_secret(namespace=namespace)
    for secret in secret_list.items:
        if secret.metadata.name == name:
            return True
    return False


def main():
    with open(os.environ["CONFIG_FILE"], "r") as in_f:
        config = json.loads(in_f.read())

    fullchain_path, privkey_path = get_certificates_path(config["tls"]["domain"])
    with open(fullchain_path, "r") as in_f:
        fullchain = in_f.read()
    with open(privkey_path, "r") as in_f:
        privkey = in_f.read()

    kclient = kubernetes.client.CoreV1Api()

    for cert_dest in config["certificates"]:
        if does_secret_exist(kclient, cert_dest["name"], cert_dest["namespace"]):
            kcall = functools.partial(kclient.replace_namespaced_secret, name=cert_dest["name"])
        else:
            kcall = kclient.create_namespaced_secret

        kcall(
            namespace=cert_dest["namespace"],
            body=kubernetes.client.V1Secret(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=cert_dest["name"],
                    namespace=cert_dest["namespace"],
                ),
                string_data={
                    "tls.crt": fullchain,
                    "tls.key": privkey,
                },
                type="kubernetes.io/tls",
            )
        )


if __name__ == "__main__":
    main()
