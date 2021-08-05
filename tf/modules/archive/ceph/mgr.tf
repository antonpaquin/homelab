resource "kubernetes_stateful_set" "ceph-mgr" {
  for_each = local.ceph_manager
  metadata {
    name = "ceph-mgr-${each.key}"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  spec {
    service_name = kubernetes_service.ceph-mgr[each.key].metadata[0].name
    selector {
      match_labels = {
        app = "ceph-mgr"
        id = each.key
      }
    }
    template {
      metadata {
        labels = {
          app = "ceph-mgr"
          id = each.key
        }
      }
      spec {
        container {
          name = "ceph"
          image = local.image
          command = ["/scripts/ceph_mgr.py"]
          args = [
            "--info-file=/config/ceph-info/info.json",
            "--secret-file=/config/ceph-secret/secret.json",
            "--mgr-data=/ceph/meta",
          ]
          env {
            name = "CEPH_HOST"
            value = each.key
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
            name = "mgr-data"
            mount_path = "/ceph/meta"
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
          name = "mgr-data"
          host_path {
            path = "/storage/meta/${each.key}"
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