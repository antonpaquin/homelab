resource "kubernetes_job" "init_pools" {
  metadata {
    name = "init-pools"
    namespace = local.namespace
  }
  spec {
    completions = 1
    template {
      metadata {
        labels = {
          app = "ceph-init-pools"
        }
      }
      spec {
        container {
          name = "ceph"
          image = local.image
          command = ["/scripts/mk_pools.py"]
          args = [
            "--info-file=/config/ceph-info/info.json",
            "--secret-file=/config/ceph-secret/secret.json",
          ]
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