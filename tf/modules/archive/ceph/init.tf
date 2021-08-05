resource "kubernetes_namespace" "ceph" {
  metadata {
    name = local.namespace
  }
}

resource "kubernetes_service" "ceph-mon" {
  for_each = local.ceph_monitor
  metadata {
    name = "ceph-mon-${each.key}"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  spec {
    selector = {
      app: "ceph-mon",
      id: each.key
    }
    cluster_ip = each.value.cluster_ip
    port {
      name = "3300"
      port = 3300
    }
    port {
      name = "6789"
      port = 6789
    }
  }
}

resource "kubernetes_service" "ceph-mgr" {
  for_each = local.ceph_manager
  metadata {
    name = "ceph-mgr-${each.key}"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  spec {
    selector = {
      app = "ceph-mgr"
      id = each.key
    }
    port {
      name = "8443"
      port = 8443
    }
  }
}

locals {
  osd_ports = range(6800, 6811)  # actually, 7300
}

resource "kubernetes_service" "ceph-osd" {
  for_each = local.osd
  metadata {
    name = "ceph-osd-${each.key}"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  spec {
    selector = {
      app: "ceph-osd"
      id: each.key
    }
    dynamic port {
      for_each = local.osd_ports
      content {
        port = port.value
        name = "${each.key}-${port.value}"
      }
    }
  }
}

resource "kubernetes_service" "ceph-mds" {
  for_each = local.mds
  metadata {
    name = "ceph-mds-${each.key}"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  spec {
    selector = {
      app = "ceph-mds"
      id = each.key
    }
    port {
      name = "8443"  # not sure if this is correct?
      port = 8443
    }
  }
}

resource "kubernetes_config_map" "ceph-info" {
  metadata {
    name = "ceph-info"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  data = {
    "info.json" = jsonencode({
      "fsid": local.fsid,
      "cluster_name": local.cluster_name,
      "mon": {
        for k, v in local.ceph_monitor:
        k => {
          cluster_ip: kubernetes_service.ceph-mon[k].spec[0].cluster_ip,
          name: k,
          role: "mon"
        }
      },
      "osd": {
        for k, v in local.osd:
        k => {
          cluster_ip: kubernetes_service.ceph-osd[k].spec[0].cluster_ip,
          name: k,
          role: "osd",
          osd_id: tostring(v["osd_id"]),
        }
      },
      "pools": local.pools,
      "crush": local.crush,
    })
  }
}

resource "kubernetes_secret" "ceph-secret" {
  metadata {
    name = "ceph-secret"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  data = {
    "secret.json": jsonencode(local.secret["ceph"])
  }
}

resource "kubernetes_config_map" "scripts" {
  metadata {
    name = "scripts"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  data = {
    "ceph_mgr.py": file("../../../modules/ceph/scripts/ceph_mgr.py")
    "ceph_mon.py": file("../../../modules/ceph/scripts/ceph_mon.py")
    "ceph_osd.py": file("../../../modules/ceph/scripts/ceph_osd.py")
    "ceph_mds.py": file("../../../modules/ceph/scripts/ceph_mds.py")
    "mk_pools.py": file("../../../modules/ceph/scripts/mk_pools.py")
    "cephconf.py": file("../../../modules/ceph/scripts/cephconf.py")
    "configure.py": file("../../../modules/ceph/scripts/configure.py")
    "keyring.py": file("../../../modules/ceph/scripts/keyring.py")
    "monmap.py": file("../../../modules/ceph/scripts/monmap.py")
    "util.py": file("../../../modules/ceph/scripts/util.py")
  }
}

locals {
  mon_list = [
    for k, v in local.ceph_monitor:
    format(
      "%s:3300",
      kubernetes_service.ceph-mon[k].spec[0].cluster_ip
    )
  ]
}
