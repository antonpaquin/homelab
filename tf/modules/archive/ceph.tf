locals {
  ceph_namespace = "default"
  ceph_image = "docker.io/ceph/ceph:v16.2"
  ceph_cluster_name = "ceph"
  ceph_storage = {
    "disk0": {host: "reimu-00", mount: "/storage/disk0"},
    "disk1": {host: "reimu-00", mount: "/storage/disk1"},
    "disk2": {host: "reimu-00", mount: "/storage/disk2"},
  }
  ceph_monitor = {
    "mon0": {},
  }
}

locals {
  _ceph_mon_member_names = join(",", keys(local.ceph_monitor))
  _ceph_mon_member_hosts = join(",", [for mon_id in keys(local.ceph_monitor): kubernetes_service.ceph-monitor[mon_id].spec[0].cluster_ip])
}

locals {
  _ceph_monmap_mon_add = join(" ", [
    for mon_id in keys(local.ceph_monitor):
    "--add ${mon_id} ${kubernetes_service.ceph-monitor[mon_id].spec[0].cluster_ip}"
  ])
  _ceph_monmap_tmpf = "/tmp/monmap_out"
  _ceph_monmap_cmd = "monmaptool --create ${local._ceph_monmap_mon_add} --fsid ${random_uuid.ceph-fs-uuid.result} ${local._ceph_monmap_tmpf}"
  _ceph_monmap_print = "${local._ceph_monmap_cmd} > /dev/null 2>&1 && cat ${local._ceph_monmap_tmpf} | base64"
  _ceph_monmap_bash = "bash -c \"${local._ceph_monmap_print}\""
}

resource "random_uuid" "ceph-fs-uuid" {
}

module "ceph-genkey-admin" {
  source = "./kubectl_cmd"
  name = "ceph-genkey-admin"
  image = local.ceph_image
  command = "ceph-authtool --gen-print-key"
}

module "ceph-genkey-mon" {
  source = "./kubectl_cmd"
  name = "ceph-genkey-mon"
  image = local.ceph_image
  command = "ceph-authtool --gen-print-key"
}

module "ceph-genkey-osd-bootstrap" {
  source = "./kubectl_cmd"
  name = "ceph-genkey-osd-bootstrap"
  image = local.ceph_image
  command = "ceph-authtool --gen-print-key"
}

module "ceph-monmap" {
  source = "./kubectl_cmd"
  name = "ceph-monmap"
  image = local.ceph_image
  command = local._ceph_monmap_bash
}

resource "kubernetes_config_map" "ceph-config" {
  metadata {
    name = "ceph"
    namespace = local.ceph_namespace
  }
  data = {
    "${local.ceph_cluster_name}.conf": <<EOF
[global]
fsid = ${random_uuid.ceph-fs-uuid.result}
public_network = 10.244.0.0/16
cluster_name = ${local.ceph_cluster_name}

mon_initial_members = ${local._ceph_mon_member_names}
mon_host = ${local._ceph_mon_member_hosts}

# TODO line

#Clusters require authentication by default.
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx

#Choose reasonable numbers for your journals, number of replicas
#and placement groups.
osd_journal_size = 1024
osd_pool_default_size = 2  # Write an object n times.
osd_pool_default_min_size = 2 # Allow writing n copy in a degraded state.
osd_pool_default_pg_num = 333
osd_pool_default_pgp_num = 333

osd_crush_chooseleaf_type = 1
EOF
    "${local.ceph_cluster_name}.keyring": <<EOF
[mon.]
	key = ${trimspace(module.ceph-genkey-mon.result)}
	caps mon = "allow *"
EOF
#    [client.admin]
#    key = ${trimspace(module.ceph-genkey-admin.result)}
#    caps mds = "allow *"
#    caps mgr = "allow *"
#    caps mon = "allow *"
#    caps osd = "allow *"
#    [client.bootstrap-osd]
#    key = ${trimspace(module.ceph-genkey-osd-bootstrap.result)}
#    caps mgr = "allow r"
#    caps mon = "profile bootstrap-osd"
  }
  binary_data = {
    "monmap": replace(trimspace(module.ceph-monmap.result), "\n", "")
  }
}

resource "kubernetes_config_map" "ceph-entrypoints" {
  metadata {
    name = "ceph-entrypoints"
    namespace = local.ceph_namespace
  }
  data = {
    "ceph-mon.sh": <<EOF
#! /usr/bin/env bash

BIND_ADDR="$(ip addr show | grep inet | grep eth0 | awk '{print $2}' | grep -o -P '([0-9]+\.){3}[0-9]+')"
export TCMALLOC_MAX_TOTAL_THREAD_CACHE_BYTES=134217728
export CEPH_AUTO_RESTART_ON_UPGRADE=no
export CLUSTER=${local.ceph_cluster_name}

sudo -u ceph ceph-mon --cluster ${local.ceph_cluster_name} --mkfs -i $CEPH_HOST --monmap /etc/ceph/monmap --keyring /etc/ceph/${local.ceph_cluster_name}.keyring
ceph-mon -f --cluster ${local.ceph_cluster_name} --id $CEPH_HOST --setuser ceph --setgroup ceph --public-bind-addr=$BIND_ADDR
EOF
  }
}

resource "kubernetes_service" "ceph-monitor" {
  for_each = local.ceph_monitor
  metadata {
    name = "ceph-monitor-${each.key}"
    namespace = local.ceph_namespace
  }
  spec {
    selector = {
      app: "ceph-monitor",
      id: each.key
    }
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

resource "kubernetes_stateful_set" "ceph-monitor" {
  for_each = local.ceph_monitor
  metadata {
    name = "ceph-monitor-${each.key}"
    namespace = local.ceph_namespace
  }
  spec {
    service_name = kubernetes_service.ceph-monitor[each.key].metadata[0].name
    selector {
      match_labels = {
        app: "ceph-monitor"
        id: each.key
      }
    }
    template {
      metadata {
        labels = {
          app: "ceph-monitor"
          id: each.key
        }
      }
      spec {
        priority_class_name = "system-cluster-critical"
        container {
          name = "ceph"
          image = local.ceph_image
          command = ["tail", "-f", "/dev/null"]
          env {
            name = "CEPH_HOST"
            value = each.key
          }
          volume_mount {
            name = "ceph-config"
            mount_path = "/etc/ceph"
          }
          volume_mount {
            name = "ceph-entrypoints"
            mount_path = "/entrypoints"
          }
        }
        volume {
          name = "ceph-config"
          config_map {
            name = kubernetes_config_map.ceph-config.metadata[0].name
          }
        }
        volume {
          name = "ceph-entrypoints"
          config_map {
            default_mode = "0777"
            name = kubernetes_config_map.ceph-entrypoints.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "ceph-storage" {
  for_each = local.ceph_storage
  metadata {
    name = "ceph-storage-${each.key}"
    namespace = local.ceph_namespace
  }
  spec {
    selector = {
      app: "ceph-storage"
      id: each.key
    }
    port {
      port = 8000
    }
  }
}

resource "kubernetes_stateful_set" "ceph-storage" {
  for_each = local.ceph_storage
  metadata {
    name = "ceph-storage-${each.key}"
    namespace = local.ceph_namespace
  }
  spec {
    service_name = kubernetes_service.ceph-storage[each.key].metadata[0].name
    selector {
      match_labels = {
        app: "ceph-storage"
        id: each.key
      }
    }
    template {
      metadata {
        labels = {
          app: "ceph-storage"
          id: each.key
        }
      }
      spec {
        node_selector = {
          "kubernetes.io/hostname": each.value.host
        }
        priority_class_name = "system-cluster-critical"
        container {
          name = "ceph"
          image = local.ceph_image
          command = ["tail", "-f", "/dev/null"]
          volume_mount {
            name = "storage"
            mount_path = "/storage"
          }
          volume_mount {
            name = "ceph-config"
            mount_path = "/etc/ceph"
          }
        }
        volume {
          name = "storage"
          host_path {
            path = each.value.mount
          }
        }
        volume {
          name = "ceph-config"
          config_map {
            name = kubernetes_config_map.ceph-config.metadata[0].name
          }
        }
      }
    }
  }
}