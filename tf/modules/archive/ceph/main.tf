locals {
  namespace = "ceph"
  # image = "docker.io/ceph/ceph:v16.2.5"
  image = "docker.io/ceph/ceph:v14.2.22"
  # 16.2.5 seems to like throwing some kind of c++ vector assertion error
  # Latest that works smoothly
  # Going back and forth between 16.2.5 and 14.2.22 seems to have tricked /storage/meta into being OK
  # Something about enabling msgr2 on 14.2 before upgrading?

  cluster_name = "ceph"

  ceph_monitor = {
    "mon0": { cluster_ip: "10.100.100.100" }
    "mon1": { cluster_ip: "10.100.100.101" },
    "mon2": { cluster_ip: "10.100.100.102" },
  }
  osd = {
    "osd0": { osd_id: 0, node: "reimu-00", mount: "/dev/sdb" },
    "osd1": { osd_id: 1, node: "reimu-00", mount: "/dev/sdc" },
    "osd2": { osd_id: 2, node: "reimu-00", mount: "/dev/sdd" },
  }
  ceph_manager = {
    "mgr0": {},
  }
  mds = {
    "mds0": {},
  }

  crush = {
  }

  pools = {
    rbd0 = {
      name = "rbd0"
      pg = 8
      application = "rbd",
      erasure = {
        n_blocks = 2
        n_parity = 1
        crush_domain = "osd"
      }
    }
    rbd0-meta = {
      name = "rbd0-meta"
      pg = 8
      application = "rbd"
      replicated = {}
    }
  }
}

data "local_file" "secret" {
  filename = "../../../secret.yaml"
}

locals {
  secret = yamldecode(data.local_file.secret.content)
  fsid = "7247e94b-b048-4a78-a625-eb44a8a09cb1"
}
