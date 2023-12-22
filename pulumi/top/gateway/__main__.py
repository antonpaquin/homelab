import yaml

from server import GatewayServer


with open('secret.yaml', 'r') as in_f:
    secrets = yaml.safe_load(in_f)


server = GatewayServer(secrets=secrets)