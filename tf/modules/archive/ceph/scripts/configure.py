#! /usr/bin/env python3

import argparse
import json
import subprocess

import cephconf
import keyring
import monmap


def setup_config(ceph_info: dict, ceph_secret: dict, keyrings: set) -> dict:
    res = {}

    b_monmap = monmap.build_monmap(ceph_info)
    monmap_file = "/etc/ceph/monmap"
    with open(monmap_file, "wb") as out_f:
        out_f.write(b_monmap)
    res["monmap"] = monmap_file

    ceph_conf = cephconf.build_config(ceph_info)
    ceph_conf_file = "/etc/ceph/ceph.conf"
    with open(ceph_conf_file, "w") as out_f:
        out_f.write(ceph_conf)
    res["cephconf"] = ceph_conf_file

    if "mon" in keyrings:
        mon_keyring = keyring.gen_mon_keyring(ceph_secret)
        mon_keyring_file = "/etc/ceph/ceph.mon.keyring"
        with open(mon_keyring_file, "w") as out_f:
            out_f.write(mon_keyring)
        res["mon_keyring"] = mon_keyring_file

    if "admin" in keyrings:
        admin_keyring = keyring.gen_admin_keyring(ceph_secret)
        admin_keyring_file = "/etc/ceph/ceph.client.admin.keyring"
        with open(admin_keyring_file, "w") as out_f:
            out_f.write(admin_keyring)
        res["admin_keyring"] = admin_keyring_file

    if "mgr" in keyrings:
        mgr_keyring = keyring.gen_mgr_keyring(ceph_secret)
        mgr_keyring_file = "/etc/ceph/ceph.mgr.keyring"
        with open(mgr_keyring_file, "w") as out_f:
            out_f.write(mgr_keyring)
        res["mgr_keyring"] = mgr_keyring_file

    if "osd" in keyrings:
        osd_keyring = keyring.gen_osd_keyring(ceph_secret)
        osd_keyring_file = "/etc/ceph/ceph.osd.keyring"
        with open(osd_keyring_file, "w") as out_f:
            out_f.write(osd_keyring)
        res["osd_keyring"] = osd_keyring_file

    if "mds" in keyrings:
        mds_keyring = keyring.gen_mds_keyring(ceph_secret)
        mds_keyring_file = "/etc/ceph/ceph.mds.keyring"
        with open(mds_keyring_file, "w") as out_f:
            out_f.write(mds_keyring)
        res["mds_keyring"] = mds_keyring_file

    return res


def cli_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--info-file")
    parser.add_argument("--secret-file")
    parser.add_argument("--halt", action="store_true")

    args = parser.parse_args()

    return {
        "info_file": args.info_file,
        "secret_file": args.secret_file,
        "halt": args.halt,
    }


def main():
    args = cli_args()

    with open(args["info_file"], "r") as in_f:
        ceph_info = json.load(in_f)

    with open(args["secret_file"], "r") as in_f:
        ceph_secret = json.load(in_f)

    print(setup_config(ceph_info, ceph_secret, keyrings={"mon", "admin", "mgr", "osd"}))

    if args["halt"]:
        subprocess.check_output(["tail", "-f", "/dev/null"])


if __name__ == "__main__":
    main()
