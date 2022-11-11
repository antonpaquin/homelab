variable "media-pvc" {
  type = string
}

variable "backup-pvc" {
  type = string
}

locals {
  namespace = "default"
}

resource "kubernetes_config_map" "shell" {
  metadata {
    name = "shell"
    namespace = local.namespace
  }
  data = {
    "entrypoint.sh": <<EOF
#! /bin/bash

useradd ubuntu
tail -f /dev/null
EOF
  }
}

resource "kubernetes_persistent_volume_claim" "shell" {
  metadata {
    name = "shell"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "shell" {
  metadata {
    name = "shell"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "shell"
      }
    }
    template {
      metadata {
        labels = {
          app = "shell"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/antonpaquin/shell:latest"
          image_pull_policy = "Always"
          command = ["/docker/entrypoint.sh"]
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
          volume_mount {
            name = "backup"
            mount_path = "/backup"
          }
          volume_mount {
            name = "shell"
            mount_path = "/home/ubuntu"
          }
          volume_mount {
            name = "config"
            mount_path = "/docker"
          }
          security_context {
            run_as_user = 1000
            run_as_group = 1000
          }
        }
        volume {
          name = "media"
          persistent_volume_claim {
            claim_name = var.media-pvc
          }
        }
        volume {
          name = "backup"
          persistent_volume_claim {
            claim_name = var.backup-pvc
          }
        }
        volume {
          name = "shell"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.shell.metadata[0].name
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.shell.metadata[0].name
            default_mode = "0755"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "shell" {
  metadata {
    name = "shell"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "shell"
    }
    port {
      port = 8000
    }
  }
}
