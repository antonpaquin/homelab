#! /usr/bin/env python3

import argparse
import json
import os
import shutil

import configure
from util import shell


def run_mgr(ceph_info: dict, ceph_secret: dict, mgr_data: str) -> None:
    config = configure.setup_config(ceph_info, ceph_secret, keyrings={"mgr"})
    mgr_id = os.environ["CEPH_HOST"]
    shutil.copy2(config["mgr_keyring"], os.path.join(mgr_data, 'keyring'))
    shell(["ceph-mgr", "-f", "--id", mgr_id, "--mgr-data", mgr_data])


def cli_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--info-file")
    parser.add_argument("--secret-file")
    parser.add_argument("--mgr-data")

    args = parser.parse_args()

    return {
        "info_file": args.info_file,
        "secret_file": args.secret_file,
        "mgr_data": args.mgr_data,
    }


def main():
    args = cli_args()

    with open(args["info_file"], "r") as in_f:
        ceph_info = json.load(in_f)

    with open(args["secret_file"], "r") as in_f:
        ceph_secret = json.load(in_f)

    run_mgr(ceph_info, ceph_secret, args["mgr_data"])


if __name__ == "__main__":
    main()
