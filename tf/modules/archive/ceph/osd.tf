resource "kubernetes_stateful_set" "ceph-osd" {
  for_each = local.osd
  metadata {
    name = "ceph-osd-${each.key}"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  spec {
    service_name = kubernetes_service.ceph-osd[each.key].metadata[0].name
    selector {
      match_labels = {
        app = "ceph-osd"
        id = each.key
      }
    }
    template {
      metadata {
        labels = {
          app = "ceph-osd"
          id = each.key
        }
      }
      spec {
        node_selector = {
          "kubernetes.io/hostname" = each.value.node
        }
        priority_class_name = "system-cluster-critical"
        container {
          name = "ceph"
          image = local.image
          command = ["/scripts/ceph_osd.py"]
          args = [
            "--info-file=/config/ceph-info/info.json",
            "--secret-file=/config/ceph-secret/secret.json",
            "--blkdev=${each.value.mount}",
          ]
          env {
            name = "CEPH_HOST"
            value = each.key
          }
          security_context {
            # oh nooo
            privileged = true
          }
          volume_mount {
            name = "ceph-info"
            mount_path = "/config/ceph-info"
          }
          volume_mount {
            name = "ceph-secret"
            mount_path = "/config/ceph-secret"
          }
          volume_mount {
            name = "scripts"
            mount_path = "/scripts"
          }
        }
        volume {
          name = "ceph-info"
          config_map {
            name = kubernetes_config_map.ceph-info.metadata[0].name
          }
        }
        volume {
          name = "ceph-secret"
          secret {
            secret_name = kubernetes_secret.ceph-secret.metadata[0].name
          }
        }
        volume {
          name = "scripts"
          config_map {
            default_mode = "0777"
            name = kubernetes_config_map.scripts.metadata[0].name
          }
        }
      }
    }
  }
}
