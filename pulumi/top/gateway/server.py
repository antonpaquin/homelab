import os

import pulumi
import pulumi_digitalocean as digitalocean

class GatewayServer(pulumi.ComponentResource):
    def __init__(
        self,
        secrets: dict,
    ):
        super().__init__("anton:server:gateway", "gateway", None, None)

        self.ssh_key = digitalocean.SshKey(
            resource_name="gateway-ssh-key",
            name="gateway-ssh-key",
            public_key=secrets["ssh"]["pubkey"],
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.droplet = digitalocean.Droplet(
            resource_name="gateway",
            name="gateway",
            region="sfo2",
            size="s-1vcpu-1gb",
            image="ubuntu-20-04-x64",
            ssh_keys=[self.ssh_key.fingerprint],
            user_data=None,  # todo: script nebula lighthouse? docker install?
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.ssh_key],
            ),
        )

