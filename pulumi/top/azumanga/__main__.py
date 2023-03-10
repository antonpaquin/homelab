"""A Python Pulumi program"""

import yaml

from cluster import create_azumanga


with open('secret.yaml', 'r') as in_f:
    secrets = yaml.safe_load(in_f)


azumanga = create_azumanga(secrets)

# azumanga.export('azumanga', )
