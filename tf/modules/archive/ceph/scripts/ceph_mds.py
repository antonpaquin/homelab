#! /usr/bin/env python3

import argparse
import json
import os
import shutil

import configure
from util import shell


def run_mds(ceph_info: dict, ceph_secret: dict, mds_data: str) -> None:
    config = configure.setup_config(ceph_info, ceph_secret, keyrings={"mds"})
    shutil.copy2(config["mds_keyring"], os.path.join(mds_data, 'keyring'))
    mds_id = os.environ["CEPH_HOST"]
    shell(["ceph-mds", "-f", "--id", mds_id, "--conf", config["cephconf"], "--mds-data", mds_data])


def cli_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--info-file")
    parser.add_argument("--secret-file")
    parser.add_argument("--mds-data")

    args = parser.parse_args()

    return {
        "info_file": args.info_file,
        "secret_file": args.secret_file,
        "mds_data": args.mds_data,
    }


def main():
    args = cli_args()

    with open(args["info_file"], "r") as in_f:
        ceph_info = json.load(in_f)

    with open(args["secret_file"], "r") as in_f:
        ceph_secret = json.load(in_f)

    run_mds(ceph_info, ceph_secret, args["mds_data"])


if __name__ == "__main__":
    main()
