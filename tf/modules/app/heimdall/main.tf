variable "domain" {
  type = string
}

variable "heimdall_apps" {
  type = list(object({
    name = string
    url = string
    image_url = string
    color = string
  }))
}

locals {
  namespace = "default"
  host = "heimdall.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "heimdall" {
  metadata {
    name = "heimdall"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "100Mi"
      }
    }
  }
}

resource "kubernetes_config_map" "heimdall" {
  metadata {
    name = "heimdall"
    namespace = local.namespace
  }
  data = {
    "apps.json": jsonencode(var.heimdall_apps)
  }
}

resource "kubernetes_deployment" "heimdall" {
  wait_for_rollout = false
  metadata {
    name = "heimdall"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "heimdall"
      }
    }
    template {
      metadata {
        name = "heimdall"
        labels = {
          app = "heimdall"
        }
      }
      spec {
        container {
          name = "main"
          image = "ghcr.io/linuxserver/heimdall:version-2.2.2"
          env {
            name = "PUID"
            value = "1000"
          }
          env {
            name = "PGID"
            value = "1000"
          }
          env {
            name = "TZ"
            value = "US/Pacific"
          }
          port {
            name = "http"
            container_port = 80
          }
          volume_mount {
            name = "config"
            mount_path = "/config/www"
          }
          # First boot sometimes takes a while to start up -- it's downloading preconfigured apps, give it some time
          # liveness_probe {
          #   timeout_seconds = 10
          #   period_seconds = 10
          #   http_get {
          #     path = "/"
          #     port = "80"
          #   }
          #   failure_threshold = 3
          # }
        }
        container {
          name = "sidecar"
          image = "docker.io/antonpaquin/misc:heimdall-sidecar"
          image_pull_policy = "Always"
          env {
            name = "HEIMDALL_SIDECAR_CONFIG_PATH"
            value = "/config/sidecar"
          }
          volume_mount {
            name = "config"
            mount_path = "/config/www"
          }
          volume_mount {
            name = "sidecar-config"
            mount_path = "/config/sidecar"
          }
        }
        volume {
          name = "config"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.heimdall.metadata[0].name
          }
        }
        volume {
          name = "sidecar-config"
          config_map {
            name = kubernetes_config_map.heimdall.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "heimdall" {
  metadata {
    name = "heimdall"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "heimdall"
    }
    port {
      name = "heimdall"
      port = 80
      target_port = "http"
    }
  }
}

resource "kubernetes_ingress_v1" "heimdall" {
  metadata {
    name = "heimdall"
    namespace = local.namespace
  }
  spec {
    ingress_class_name = "nginx"
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service {
              name = kubernetes_service.heimdall.metadata[0].name
              port {
                name = "heimdall"
              }
            }
          }
        }
      }
    }
  }
}

output "host" {
  value = local.host
}
