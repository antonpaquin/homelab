locals {
  namespace = "default"
}

resource "kubernetes_service_account" "cadvisor" {
  metadata {
    name = "cadvisor"
    namespace = local.namespace
  }
}

resource "kubernetes_daemonset" "cadvisor" {
  metadata {
    name = "cadvisor"
    namespace = local.namespace
    annotations = {
      "seccomp.security.alpha.kubernetes.io/pod" = "docker/default"
    }
  }
  spec {
    selector {
      match_labels = {
        name = "cadvisor"
      }
    }
    template {
      metadata {
        labels = {
          name = "cadvisor"
        }
      }
      spec {
        service_account_name = kubernetes_service_account.cadvisor.metadata[0].name
        container {
          name = "cadvisor"
          image = "gcr.io/cadvisor/cadvisor:v0.39.0"
          resources {
            requests = {
              memory = "400Mi"
              cpu = "400m"
            }
            limits = {
              memory = "2000Mi"
              cpu = "800m"
            }
          }
          volume_mount {
            name = "rootfs"
            mount_path = "/rootfs"
            read_only = true
          }
          volume_mount {
            name = "var-run"
            mount_path = "/var/run"
            read_only = true
          }
          volume_mount {
            name = "sys"
            mount_path = "/sys"
            read_only = true
          }
          volume_mount {
            name = "docker"
            mount_path = "/var/lib/docker"
            read_only = true
          }
          volume_mount {
            name = "disk"
            mount_path = "/dev/disk"
            read_only = true
          }
          port {
            name = "http"
            container_port = 8080
            protocol = "TCP"
          }
        }
        automount_service_account_token = false
        termination_grace_period_seconds = 30
        volume {
          name = "rootfs"
          host_path {
            path = "/"
          }
        }
        volume {
          name = "var-run"
          host_path {
            path = "/var/run"
          }
        }
        volume {
          name = "sys"
          host_path {
            path = "/sys"
          }
        }
        volume {
          name = "docker"
          host_path {
            path = "/var/lib/docker"
          }
        }
        volume {
          name = "disk"
          host_path {
            path = "/dev/disk"
          }
        }
      }
    }
  }
}
