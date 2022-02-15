variable "domain" {
  type = string
}

variable "keycloak-oidc" {
  type = object({
    client-id: string
    client-secret: string
  })
  description = "Give some placeholder initially, then set up in the keycloak webui. See https://wjw465150.gitbooks.io/keycloak-documentation/content/server_admin/topics/clients/client-oidc.html (+ subpages, esp 3.8.1.1)"
}

variable "namespace" {
  type = string
  default = "Namespace under which to run the authproxy server"
}

variable "authproxy_host" {
  type = string
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
      issuer_url: "http://keycloak.${var.domain}/auth/realms/default/",
      redirect_uri: "http://${var.authproxy_host}/auth",
      client_id: var.keycloak-oidc.client-id
      client_secret: var.keycloak-oidc.client-secret
      protected_domains: local.protected-domains,
      authproxy_endpoint: local.authproxy_endpoint,
      key_seed: random_password.authproxy_key_seed.result,
      db_path: "/tmp/authproxy.sqlite",
    })
  }
}

resource "kubernetes_deployment" "authproxy" {
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
    namespace = var.namespace
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
    namespace = var.namespace
  }
  spec {
    rule {
      host = var.authproxy_host
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
  value = var.authproxy_host
}