variable "init_drives" {
  type = bool
  default = false
}

locals {
  namespace = "rook-ceph"
  storage = {
    "disk0": {
      node: "reimu-00"  # For now: requires SSH to nodes as part of the provisioner
      device: "/dev/sdb"
      capacity: "3726Gi"
    }
    "disk1": {
      node: "reimu-00"
      device: "/dev/sdc"
      capacity: "3726Gi"
    }
    "disk2": {
      node: "reimu-00"
      device: "/dev/sdd"
      capacity: "3726Gi"
    }
  }
  meta = {
    node: "reimu-00"  # TODO: how to ensure the cluster listens to this?
    path: "/storage/meta"
  }
  mons = {
    # Open loop controls: these just happen to be the names of the services that the CephCluster manifest will create
    # Doesn't map neatly to storage nodes -- this is set by spec.mon.count
    "a": {name: "rook-ceph-mon-a"}
    "b": {name: "rook-ceph-mon-b"}
    "c": {name: "rook-ceph-mon-c"}
  }
}

# TODO: how to sequence steps at the module level?
#   e.g. 00, waiter, 01, ...
# TODO: test: do RBD volumes survive a teardown?
# TODO: properly derive cluster ID in "provisioner.tf"
