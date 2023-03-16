"""A Python Pulumi program"""

import yaml

from cluster import AzumangaCluster
from config import Nodes


with open('secret.yaml', 'r') as in_f:
    secrets = yaml.safe_load(in_f)

azumanga = AzumangaCluster(
    secrets=secrets,
    storage_node=Nodes.osaka,
)

# azumanga.export('azumanga', )
