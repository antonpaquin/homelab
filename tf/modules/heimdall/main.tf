variable "domain" {
  type = string
  default = "k8s.local"
}

locals {
  namespace = "default"
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

resource "kubernetes_deployment" "heimdall" {
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
          volume_mount {
            name = "config"
            mount_path = "/config/www"
          }
        }
        volume {
          name = "config"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.heimdall.metadata[0].name
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
    }
  }
}

resource "kubernetes_ingress" "heimdall" {
  metadata {
    name = "heimdall"
    namespace = local.namespace
  }
  spec {
    rule {
      host = "heimdall.${var.domain}"
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.heimdall.metadata[0].name
            service_port = "heimdall"
          }
        }
      }
    }
  }
}

