#! /usr/bin/env python3


mon_template = '''
[mon.]
	key = {mon_secret}
	caps mon = "allow *"

[client.admin]
	key = {admin_secret}
	caps mds = "allow *"
	caps mon = "allow *"
	caps osd = "allow *"
	caps mgr = "allow *"

[mgr.mgr0]
	key = {mgr_secret}
	caps mon = "allow profile mgr"
	caps osd = "allow *"
	caps mds = "allow *"

[client.bootstrap-osd]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"

[osd.0]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"

[osd.1]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"

[osd.2]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"

[mds.mds0]
    key = {mds_secret}
	caps mon = "allow profile mds"
	caps mds = "allow *"
	caps osd = "allow rwx"
'''.lstrip()


def gen_mon_keyring(ceph_secret: dict) -> str:
    return mon_template.format(
        mon_secret=ceph_secret["mon-secret"],
        admin_secret=ceph_secret["admin-secret"],
        mgr_secret=ceph_secret["mgr-secret"],
        osd_secret=ceph_secret["osd-secret"],
        mds_secret=ceph_secret["mds-secret"],
    )


admin_template = '''
[client.admin]
	key = {admin_secret}
	caps mds = "allow *"
	caps mon = "allow *"
	caps osd = "allow *"
	caps mgr = "allow *"
'''.lstrip()


def gen_admin_keyring(ceph_secret: dict) -> str:
    return admin_template.format(
        admin_secret=ceph_secret["admin-secret"],
    )


mgr_template = '''
[mgr.mgr0]
	key = {mgr_secret}
	caps mon = "allow profile mgr"
	caps osd = "allow *"
	caps mds = "allow *"
'''.lstrip()


def gen_mgr_keyring(ceph_secret: dict) -> str:
    return mgr_template.format(
        mgr_secret=ceph_secret["mgr-secret"],
    )


osd_template = '''
[client.bootstrap-osd]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"

[osd.0]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"

[osd.1]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"

[osd.2]
	key = {osd_secret}
	caps osd = "allow *"
	caps mon = "allow *"
'''.lstrip()


def gen_osd_keyring(ceph_secret: dict) -> str:
    return osd_template.format(
        osd_secret=ceph_secret["osd-secret"],
    )


mds_template = '''
[mds.mds0]
	key = {mds_secret}
	caps mon = "allow profile mds"
	caps mds = "allow *"
	caps osd = "allow rwx"
'''.lstrip()


def gen_mds_keyring(ceph_secret: dict) -> str:
    return mds_template.format(
        mds_secret=ceph_secret["mds-secret"],
    )
