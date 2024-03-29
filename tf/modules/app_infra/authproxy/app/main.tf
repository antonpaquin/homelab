variable "domain" {
  type = string
}

variable "keycloak" {
  type = object({
    oidc = object({
      # "Give some placeholder initially, then set up in the keycloak webui. See https://wjw465150.gitbooks.io/keycloak-documentation/content/server_admin/topics/clients/client-oidc.html (+ subpages, esp 3.8.1.1)"
      client-id: string
      client-secret: string
    })
    service = object({
      name = string
      namespace = string
      port = string
    })
  })
  description = "keycloak info"
}

variable "namespace" {
  type = string
  default = "Namespace under which to run the authproxy server"
}

variable "authproxy_host" {
  type = string
}

variable "tls_secret" {
  type = string
  description = "Secret containing a wildcard certificate of the type kubernetes.io/tls"
}

locals {
  authproxy_endpoint = "/_authproxy"
}

resource "random_password" "authproxy_key_seed" {
  length = 30
}

resource "kubernetes_secret" "auth_proxy_config" {
  metadata {
    name = "auth-proxy-config"
    namespace = var.namespace
  }
  data = {
    "config.json": jsonencode({
      issuer_url: "http://${var.keycloak.service.name}.${var.keycloak.service.namespace}.svc.cluster.local:${var.keycloak.service.port}/realms/default",
      redirect_uri: "https://${var.authproxy_host}/auth",
      client_id: var.keycloak.oidc.client-id
      client_secret: var.keycloak.oidc.client-secret
      protected_domains: local.protected-domains,
      authproxy_endpoint: local.authproxy_endpoint,
      key_seed: random_password.authproxy_key_seed.result,
      db_path: "/tmp/authproxy.sqlite",
    })
  }
}

resource "kubernetes_deployment" "authproxy" {
  wait_for_rollout = false
  metadata {
    name = "authproxy"
    namespace = var.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "authproxy"
      }
    }
    template {
      metadata {
        labels = {
          app = "authproxy"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/antonpaquin/misc:authproxy"
          image_pull_policy = "Always"
          env {
            name = "APP_HOST"
            value = "0.0.0.0"
          }
          env {
            name = "APP_PORT"
            value = "4000"
          }
          env {
            name = "AUTH_PROXY_CONFIG"
            value = "/etc/authproxy/config.json"
          }
          volume_mount {
            name = "config"
            mount_path = "/etc/authproxy/"
          }
        }
        volume {
          name = "config"
          secret {
            secret_name = kubernetes_secret.auth_proxy_config.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "authproxy" {
  metadata {
    name = "authproxy"
    namespace = var.namespace
  }
  spec {
    selector = {
      app = "authproxy"
    }
    port {
      port = 80
      name = "http"
      target_port = 4000
    }
  }
}

resource "kubernetes_ingress_v1" "authproxy" {
  metadata {
    name = "authproxy"
    namespace = var.namespace
  }
  spec {
    ingress_class_name = "nginx"
    tls {
      secret_name = var.tls_secret
    }
    rule {
      host = var.authproxy_host
      http {
        path {
          path = "/"
          backend {
            service {
              name = kubernetes_service.authproxy.metadata[0].name
              port {
                name = "http"
              }
            }
          }
        }
      }
    }
  }
}

output "host" {
  value = var.authproxy_host
}