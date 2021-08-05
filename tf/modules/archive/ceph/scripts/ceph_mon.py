#! /usr/bin/env python3

import argparse
import json
import os

import configure
from util import shell, get_bind_addr


def msgr2():
    shell(["ceph", "mon", "enable-msgr2"])


def mkfs(ceph_config: dict, cluster_name: str, mon_id: str, bind_addr: str, mon_data: str) -> None:
    cmd = ["sudo", "-u", "ceph", "ceph-mon"]
    cmd.extend(["--cluster", cluster_name])
    cmd.extend(["--mkfs"])
    cmd.extend(["--id", mon_id])
    cmd.extend(["--monmap",  ceph_config["monmap"]])
    cmd.extend(["--keyring", ceph_config["mon_keyring"]])
    cmd.extend(["--conf", ceph_config["cephconf"]])
    cmd.extend(["--mon-data", mon_data])
    cmd.extend(["--public-bind-addr", bind_addr])

    shell(cmd)


def run_mon(ceph_config: dict, cluster_name: str, mon_id: str, bind_addr: str, mon_data: str) -> None:
    cmd = ["sudo", "-u", "ceph", "ceph-mon", "-f"]
    cmd.extend(["--cluster", cluster_name])
    cmd.extend(["--id", mon_id])
    cmd.extend(["--monmap", ceph_config["monmap"]])
    cmd.extend(["--keyring", ceph_config["mon_keyring"]])
    cmd.extend(["--conf", ceph_config["cephconf"]])
    cmd.extend(["--mon-data", mon_data])
    cmd.extend(["--public-bind-addr", bind_addr])

    shell(cmd)


def ceph_mon(info_file: str, secret_file: str, mon_data: str):
    with open(info_file, 'r') as in_f:
        ceph_info = json.load(in_f)

    with open(secret_file, 'r') as in_f:
        ceph_secret = json.load(in_f)

    ceph_config = configure.setup_config(ceph_info, ceph_secret, keyrings={'mon', 'admin'})

    cluster_name = ceph_info["cluster_name"]
    mon_id = os.environ["CEPH_HOST"]
    bind_addr = get_bind_addr()

    if os.path.exists(mon_data):
        shell(["chown", "-R", "ceph:ceph", mon_data])

    mkfs(ceph_config, cluster_name, mon_id, bind_addr, mon_data)
    run_mon(ceph_config, cluster_name, mon_id, bind_addr, mon_data)


def cli_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--info-file")
    parser.add_argument("--secret-file")
    parser.add_argument("--mon-data")

    args = parser.parse_args()

    return {
        "info_file": args.info_file,
        "secret_file": args.secret_file,
        "mon_data": args.mon_data,
    }


if __name__ == "__main__":
    args = cli_args()
    ceph_mon(args["info_file"], args["secret_file"], args["mon_data"])
