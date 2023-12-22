import os
import yaml


with open('secret.yaml', 'r') as in_f:
    secrets = yaml.safe_load(in_f)


from server import GatewayServer
server = GatewayServer(secrets=secrets)