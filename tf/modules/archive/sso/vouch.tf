locals {
  vouch_port = 9090
}

resource "kubernetes_secret" "vouch" {
  metadata {
    name = "vouch"
    namespace = local.namespace
  }
  data = {
    "config.yml" = <<EOF
vouch:
  allowAllUsers: true

  cookie:
    secure: false
    domain: ${var.domain}

  headers:
    claims:
      - sub

oauth:
  provider: oidc
  client_id: authproxy-oidc
  client_secret: ${var.keycloak-oidc-secret}
  auth_url: http://keycloak.k8s.local/auth/realms/default/protocol/openid-connect/auth
  token_url: http://keycloak.k8s.local/auth/realms/default/protocol/openid-connect/token
  user_info_url: http://keycloak.k8s.local/auth/realms/default/protocol/openid-connect/userinfo
  scopes:
    - openid
    - email
    - profile
  callback_url: http://vouch.k8s.local/auth
EOF
  }
}

resource "kubernetes_deployment" "vouch" {
  metadata {
    name = "vouch"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "vouch"
      }
    }
    template {
      metadata {
        labels = {
          app = "vouch"
        }
      }
      spec {
        container {
          name = "main"
          image = "voucher/vouch-proxy:0.27.1"
          env {
            name = "VOUCH_PORT"
            value = local.vouch_port
          }
          volume_mount {
            name = "vouch-config"
            mount_path = "/config"
            read_only = false
          }
        }
        volume {
          name = "vouch-config"
          secret {
            secret_name = kubernetes_secret.vouch.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "vouch" {
  metadata {
    name = "vouch"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "vouch"
    }
    port {
      port = 9090
      name = "http"
    }
  }
}

resource "kubernetes_ingress_v1" "vouch" {
  metadata {
    name = "vouch"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.vouch_host
      http {
        path {
          path = "/"
          backend {
            service {
              name = kubernetes_service.vouch.metadata[0].name
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
