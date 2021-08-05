#! /usr/bin/env python3

import argparse
import base64
import json
import tempfile
from typing import List, Tuple
import subprocess


def monmap_create(mons: List[Tuple[str, str]], fsid: str) -> bytes:
    cmd = ["monmaptool", "--create"]
    for mon_id, mon_ip in mons:
        cmd.extend(["--addv", mon_id, f'v2:{mon_ip}:3300'])

    cmd.extend(["--fsid", fsid])

    output_file = tempfile.mktemp('.out')
    cmd.append(output_file)

    subprocess.check_output(cmd)

    with open(output_file, 'rb') as in_f:
        result = in_f.read()

    return result


def build_monmap(ceph_info: dict) -> bytes:
    mons = [(mon_spec['name'], mon_spec['cluster_ip']) for _, mon_spec in ceph_info['mon'].items()]
    fsid = ceph_info["fsid"]
    return monmap_create(mons, fsid)


def main(info_file: str) -> str:
    with open(info_file, 'r') as in_f:
        ceph_info = json.load(in_f)
    return base64.b64encode(build_monmap(ceph_info)).decode('utf-8')


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