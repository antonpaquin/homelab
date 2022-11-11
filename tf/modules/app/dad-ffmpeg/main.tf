locals {
  namespace = "default"
}

resource "kubernetes_service" "dad-ffmpeg" {
  metadata {
    name = "dad-ffmpeg"
    namespace = local.namespace
  }
  spec {
    type = "NodePort"
    selector = {
      app = "dad-ffmpeg"
    }
    port {
      port = 22
      node_port = 10022
    }
  }
}

resource "kubernetes_persistent_volume_claim" "dad-ffmpeg" {
  metadata {
    name = "dad-ffmpeg"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "200Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "dad-ffmpeg" {
  metadata {
    name = "dad-ffmpeg"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "dad-ffmpeg"
      }
    }
    template {
      metadata {
        labels = {
          app = "dad-ffmpeg"
        }
      }
      spec {
        container {
          name = "ffmpeg"
          image = "docker.io/antonpaquin/misc:dad-ffmpeg"
          command = ["/entrypoint.sh"]
          volume_mount {
            name = "storage"
            mount_path = "/data"
          }
          security_context {
            capabilities {
              add = ["NET_ADMIN", "SYS_ADMIN", "DAC_READ_SEARCH"]
            }
          }

        }
        volume {
          name = "storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.dad-ffmpeg.metadata[0].name
          }
        }
      }
    }
  }
}