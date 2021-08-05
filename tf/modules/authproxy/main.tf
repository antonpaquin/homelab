variable "domain" {
  type = string
  default = "k8s.local"
}

variable "keycloak-oidc-secret" {
  type = string
  description = "Give some placeholder initially, then set up in the keycloak webui. See https://wjw465150.gitbooks.io/keycloak-documentation/content/server_admin/topics/clients/client-oidc.html (+ subpages, esp 3.8.1.1)"
}

variable "protected-domains" {
  type = list(object({
    domain = string
    role = string
    auth_request = any
  }))
}

locals {
  namespace = "default"
  host = "authproxy.${var.domain}"
}

resource "kubernetes_secret" "auth_proxy_config" {
  metadata {
    name = "auth-proxy-config"
    namespace = local.namespace
  }
  data = {
    "config.json": jsonencode({
      "issuer_url": "http://keycloak.k8s.local/auth/realms/default/",
      "redirect_uri": "http://authproxy.${var.domain}/auth",
      "client_id": "authproxy-oidc",
      "client_secret": var.keycloak-oidc-secret,
      "protected_domains": var.protected-domains,
    })
  }
}

resource "kubernetes_deployment" "authproxy" {
  metadata {
    name = "authproxy"
    namespace = local.namespace
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
          image = "antonpaquin/misc:authproxy"
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
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "authproxy"
    }
    port {
      port = 4000
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "authproxy" {
  metadata {
    name = "authproxy"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.authproxy.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}

output "host" {
  value = local.host
}