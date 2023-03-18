"""A Python Pulumi program"""

import yaml

from cluster import AzumangaCluster
from config import Nodes


with open('secret.yaml', 'r') as in_f:
    secrets = yaml.safe_load(in_f)

secrets['ssl'] = {}

with open('secret/ssl.crt', 'r') as in_f:
    secrets['ssl']['crt'] = in_f.read()

with open('secret/ssl.key', 'r') as in_f:
    secrets['ssl']['key'] = in_f.read()

azumanga = AzumangaCluster(
    secrets=secrets,
    storage_node=Nodes.osaka,
)

# azumanga.export('azumanga', )
