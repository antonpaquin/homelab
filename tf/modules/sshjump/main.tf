variable "private-key" {
  type = string
  description = "private key to the jump ssh user"
}

variable "remote-user" {
  type = string
  description = "Username for the remote user that will forward traffic"
}

variable "remote-port" {
  type = string
  description = "Port for the SSH connection (Not port for traffic; that will be 80/443)"
}

variable "remote-host" {
  type = string
  description = "Remote machine with public IP that we can connect from"
  # Note: ensure `GatewayPorts yes` is in /etc/ssh/sshd_config on the gateway server
}

variable "forward-destination" {
  type = string
  description = "Forward traffic to this destination"
}

locals {
  namespace = "kube-system"
}

resource "kubernetes_secret" "ssh-jump" {
  metadata {
    name = "sshjump"
    namespace = local.namespace
  }
  data = {
    "config": join("\n", [
      "Host sshjump",
      "    HostName ${var.remote-host}",
      "    User ${var.remote-user}",
      "    Port ${var.remote-port}",
      "    IdentityFile ~/.ssh/key.pem",
    ])
    "key.pem": "${var.private-key}\n"
  }
}

resource "kubernetes_service" "ssh-jump" {
  metadata {
    name = "ssh-jump"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "ssh-jump"
    }
    port {
      port = 3123
    }
  }
}

resource "kubernetes_stateful_set" "ssh-jump" {
  metadata {
    name = "ssh-jump"
    namespace = local.namespace
  }
  spec {
    service_name = kubernetes_service.ssh-jump.metadata[0].name
    selector {
      match_labels = {
        app = "ssh-jump"
      }
    }
    template {
      metadata {
        labels = {
          app = "ssh-jump"
        }
      }
      spec {
        container {
          name = "main"
          image = "antonpaquin/misc:sshjump"
          image_pull_policy = "Always"
          env {
            name = "DEST"
            value = var.forward-destination
          }
          volume_mount {
            name = "ssh-conf"
            mount_path = "/root/.ssh"
          }
        }
        volume {
          name = "ssh-conf"
          secret {
            secret_name = kubernetes_secret.ssh-jump.metadata[0].name
            items {
              key = "config"
              mode = "0400"
              path = "config"
            }
            items {
              key = "key.pem"
              mode = "0400"
              path = "key.pem"
            }
          }
        }
      }
    }
  }
}
