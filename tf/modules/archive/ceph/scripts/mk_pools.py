#! /usr/bin/env python3

import argparse
import json
import re
import subprocess
import time

import configure
from util import shell


def mk_pools(ceph_info: dict, ceph_secret: dict) -> None:
    configure.setup_config(ceph_info, ceph_secret, keyrings={"admin"})
    pool_info = ceph_info["pools"]

    await_osd(ceph_info)

    for _, pool_spec in pool_info.items():
        pool_name = pool_spec["name"]
        try:
            shell(["ceph", "osd", "pool", "stats", pool_name])
        except subprocess.CalledProcessError:
            mk_pool(pool_name, pool_spec)


def await_osd(ceph_info: dict):
    parse_osd_stat = re.compile(r'^([0-9]+) osds: ([0-9]+) up \(since .*\), ([0-9]+) in \(since .*\); epoch: .*$')

    wanted_osd = len(ceph_info["osd"])
    observed_osd = 0

    while observed_osd != wanted_osd:
        osd_stat = shell(["ceph", "osd", "stat"]).decode("ascii").strip()
        groups = parse_osd_stat.match(osd_stat).groups()
        joined_osd, up_osd, in_osd = map(int, groups)
        observed_osd = min(up_osd, in_osd)
        if observed_osd != wanted_osd:
            time.sleep(3)


def mk_pool(name: str, info: dict):
    pg_num = info["pg"]

    if "erasure" in info:
        n_blocks = info["erasure"]["n_blocks"]
        n_parity = info["erasure"]["n_parity"]
        crush_domain = info["erasure"]["crush_domain"]
        mk_erasure_pool(name, pg_num, n_blocks, n_parity, crush_domain)
    elif "replicated" in info:
        mk_replicated_pool(name, pg_num)
    else:
        raise NotImplementedError('Missing case')

    shell(["ceph", "osd", "pool", "set", name, "pg_autoscale_mode", "on"])

    if info["application"] == "rbd":
        shell(["rbd", "pool", "init", name])
    else:
        raise NotImplementedError('Missing case')



def mk_replicated_pool(name: str, pg_num: int):
    cmd = ["ceph", "osd", "pool", "create"]
    cmd.extend([name, str(pg_num)]),
    cmd.extend(["replicated"])
    shell(cmd)


def mk_erasure_pool(name: str, pg_num: int, erasure_n_blocks: int, erasure_n_parity: int, crush_failure_domain: str):
    erasure_profile_name = f"{name}-erasureprofile"
    try:
        shell(["ceph", "osd", "erasure-code-profile", "get", erasure_profile_name])
    except subprocess.CalledProcessError:
        cmd = ["ceph", "osd", "erasure-code-profile", "set"]
        cmd.extend([erasure_profile_name])
        cmd.extend([f"k={erasure_n_blocks}"])
        cmd.extend([f"m={erasure_n_parity}"])
        cmd.extend([f"crush-failure-domain={crush_failure_domain}"])
        shell(cmd)

    cmd = ["ceph", "osd", "pool", "create"]
    cmd.extend([name, str(pg_num)])
    cmd.extend(["erasure", erasure_profile_name])
    shell(cmd)

def cli_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--info-file")
    parser.add_argument("--secret-file")

    args = parser.parse_args()

    return {
        "info_file": args.info_file,
        "secret_file": args.secret_file,
    }


def main():
    args = cli_args()

    with open(args["info_file"], "r") as in_f:
        ceph_info = json.load(in_f)

    with open(args["secret_file"], "r") as in_f:
        ceph_secret = json.load(in_f)

    mk_pools(ceph_info, ceph_secret)


if __name__ == "__main__":
    main()
