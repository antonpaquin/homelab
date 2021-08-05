#! /usr/bin/env python3

import argparse
import base64
import json
import os
import shutil
import time

import configure
from util import shell, get_bind_addr


def run_osd_bak(ceph_info: dict, ceph_secret: dict, osd_data: str) -> None:
    config = configure.setup_config(ceph_info, ceph_secret, keyrings={"osd"})
    osd_id = os.environ["CEPH_HOST"]
    shutil.copy2(config[f"osd_keyring"], os.path.join(osd_data, "keyring"))

    osd_uid = ceph_info["osd"][osd_id]["uuid"]
    osd_idx = ceph_info["osd"][osd_id]["osd_id"]
    bind_addr = get_bind_addr()
    keyring_file = config["osd_keyring"]


    cmd = ["ceph", "osd", "new"]
    cmd.extend([osd_uid])
    cmd.extend(["-n", f"osd.{osd_idx}"])
    cmd.extend(["--keyring", keyring_file])
    cmd.extend(["--osd-data", osd_data])
    shell(cmd)

    cmd = ["ceph-osd"]
    cmd.extend(["-i", osd_idx])
    cmd.extend(["--mkfs"])
    cmd.extend(["--osd-uuid", osd_uid])
    cmd.extend(["--osd-data", osd_data])
    cmd.extend(["--public-bind-addr", bind_addr])
    shell(cmd)

    shell(["chown", "-R", "ceph:ceph", osd_data])

    cmd = ["ceph-osd", "-f"]
    cmd.extend(["-i", osd_idx])
    cmd.extend(["--osd-uuid", osd_uid])
    cmd.extend(["--osd-data", osd_data])
    cmd.extend(["--public-bind-addr", bind_addr])
    shell(cmd)


def get_n_osd():
    cmd = ["ceph", "osd", "ls"]
    out = shell(cmd).decode('ascii').strip()
    print(out.split('\n'))
    return len(out.split('\n'))


def init_osd(osd_idx, blkdev):
    while get_n_osd() < osd_idx:
        time.sleep(3)
    time.sleep(3)
    shell(["ceph-volume", "raw", "prepare", "--bluestore", "--data", blkdev])



def run_osd(ceph_info: dict, ceph_secret: dict, blkdev: str) -> None:
    configure.setup_config(ceph_info, ceph_secret, keyrings={"osd"})
    osd_id = os.environ["CEPH_HOST"]

    osd_idx = int(ceph_info["osd"][osd_id]["osd_id"])

    try:
        shell(["ceph-bluestore-tool", "show-label", "--dev", blkdev])
    except Exception:
        init_osd(osd_idx, blkdev)

    shell(["ceph-volume", "raw", "activate", "--no-systemd", "--device", blkdev])
    shell(["ceph-osd", "-f", "-i", str(osd_idx)])


def cli_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--info-file")
    parser.add_argument("--secret-file")
    parser.add_argument("--blkdev")

    args = parser.parse_args()

    return {
        "info_file": args.info_file,
        "secret_file": args.secret_file,
        "blkdev": args.blkdev,
    }


def main():
    args = cli_args()

    with open(args["info_file"], "r") as in_f:
        ceph_info = json.load(in_f)

    with open(args["secret_file"], "r") as in_f:
        ceph_secret = json.load(in_f)

    run_osd(ceph_info, ceph_secret, args["blkdev"])


if __name__ == "__main__":
    main()
