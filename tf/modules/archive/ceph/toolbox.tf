resource "kubernetes_deployment" "toolbox" {
  metadata {
    name = "toolbox"
    namespace = kubernetes_namespace.ceph.metadata[0].name
  }
  spec {
    selector {
      match_labels = {
        app = "ceph"
        role = "toolbox"
      }
    }
    template {
      metadata {
        labels = {
          app = "ceph"
          role = "toolbox"
        }
      }
      spec {
        container {
          name = "main"
          image = local.image
          command = ["/scripts/configure.py"]
          args = [
            "--info-file=/config/ceph-info/info.json",
            "--secret-file=/config/ceph-secret/secret.json",
            "--halt",
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
