variable "init_drives" {
  type = bool
}

locals {
  namespace = "rook"
  storage = {
    "disk0": {
      node: "reimu-00"  # For now: requires SSH to nodes as part of the provisioner
      device: "/dev/sdd"
      capacity: "3726Gi"
    }
    "disk1": {
      node: "reimu-00"
      device: "/dev/sde"
      capacity: "3726Gi"
    }
    "disk2": {
      node: "reimu-00"
      device: "/dev/sdf"
      capacity: "3726Gi"
    }
  }
  meta = {
    node: "reimu-00"  # TODO: how to ensure the cluster listens to this?
    path: "/storage/meta"
  }
}

# TODO: how to sequence steps at the module level?
#   e.g. 00, waiter, 01, ...
# TODO: test: do RBD volumes survive a teardown?
# TODO: properly derive cluster ID in "provisioner.tf"
