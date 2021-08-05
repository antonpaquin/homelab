#! /usr/bin/env python3

import argparse
import json


config_template = '''
[global]
fsid = {fsid}
public_network = 10.244.0.0/16
cluster_name = {cluster_name}

mon_initial_members = {mon_initial_members}
mon_host = {mon_hosts}

auth_cluster_required = none
auth_service_required = none
auth_client_required = none
auth_allow_insecure_global_id_reclaim = false

osd_journal_size = 1024
osd_pool_default_size = 2  # Write an object n times.
osd_pool_default_min_size = 2 # Allow writing n copy in a degraded state.
osd_pool_default_pg_num = 333
osd_pool_default_pgp_num = 333

osd_crush_chooseleaf_type = 1
'''


def build_config(ceph_info: dict) -> str:
    mons = [ceph_info['mon'][mon] for mon in sorted(ceph_info['mon'].keys())]
    mon_initial_members = ','.join([mon['name'] for mon in mons])
    mon_hosts = ','.join([mon['cluster_ip'] for mon in mons])

    return config_template.format(
        fsid=ceph_info['fsid'],
        cluster_name=ceph_info['cluster_name'],
        mon_initial_members=mon_initial_members,
        mon_hosts=mon_hosts,
    )


def main(info_file: str) -> str:
    with open(info_file, 'r') as in_f:
        ceph_info = json.load(in_f)
    return build_config(ceph_info)


def cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--info-file")
    args = parser.parse_args()
    return {
        "info_file": args.info_file,
    }


if __name__ == "__main__":
    args = cli_args()
    print(main(args["info_file"]))
