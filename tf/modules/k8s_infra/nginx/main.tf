locals {
  ports = {
    http: {
      port: 80
      name: "http"
      proto: "TCP"
    }
    https: {
      port: 443
      name: "https"
      proto: "TCP"
    }
    # Disabled: apparently better to use nodeport?
    # federation: {
    #   # Is this standard or just synapse?
    #   port: 8448
    #   name: "federation"
    #   proto: "TCP"
    # }
  }
}

resource "kubernetes_namespace" "ingress_nginx" {
  metadata {
    name = "ingress-nginx"
    labels = {
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
    }
  }
}

resource "kubernetes_service_account" "ingress_nginx" {
  metadata {
    name      = "ingress-nginx"
    namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
    labels = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/part-of" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
    }
  }
  automount_service_account_token = true
}

resource "kubernetes_config_map" "ingress_nginx_controller" {
  metadata {
    name      = "ingress-nginx-controller"
    namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
    labels = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/part-of" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
    }
  }
  data = {
    "allow-snippet-annotations" = "true"
    "hsts" = false
  }
}

resource "kubernetes_cluster_role" "ingress_nginx" {
  metadata {
    name = "ingress-nginx"
    labels = {
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
      "app.kubernetes.io/part-of" = "ingress-nginx"
    }
  }
  rule {
    verbs      = ["list", "watch"]
    api_groups = [""]
    resources  = ["configmaps", "endpoints", "nodes", "pods", "secrets", "namespaces"]
  }
  rule {
    verbs      = ["list", "watch"]
    api_groups = ["coordination.k8s.io"]
    resources  = ["leases"]
  }
  rule {
    verbs      = ["get"]
    api_groups = [""]
    resources  = ["nodes"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = [""]
    resources  = ["services"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = ["networking.k8s.io"]
    resources  = ["ingresses"]
  }
  rule {
    verbs      = ["create", "patch"]
    api_groups = [""]
    resources  = ["events"]
  }
  rule {
    verbs      = ["update"]
    api_groups = ["networking.k8s.io"]
    resources  = ["ingresses/status"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = ["networking.k8s.io"]
    resources  = ["ingressclasses"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = ["discovery.k8s.io"]
    resources  = ["endpointslices"]
  }
}

resource "kubernetes_cluster_role_binding" "ingress_nginx" {
  metadata {
    name = "ingress-nginx"
    labels = {
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
      "app.kubernetes.io/part-of" = "ingress-nginx"
    }
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.ingress_nginx.metadata[0].name
    namespace = kubernetes_service_account.ingress_nginx.metadata[0].namespace
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.ingress_nginx.metadata[0].name
  }
}

resource "kubernetes_role" "ingress_nginx" {
  metadata {
    name      = "ingress-nginx"
    namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
    labels = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
      "app.kubernetes.io/part-of" = "ingress-nginx"
    }
  }
  rule {
    verbs      = ["get"]
    api_groups = [""]
    resources  = ["namespaces"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = [""]
    resources  = ["configmaps", "pods", "secrets", "endpoints"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = [""]
    resources  = ["services"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = ["networking.k8s.io"]
    resources  = ["ingresses"]
  }
  rule {
    verbs      = ["update"]
    api_groups = ["networking.k8s.io"]
    resources  = ["ingresses/status"]
  }
  rule {
    verbs      = ["get", "list", "watch"]
    api_groups = ["networking.k8s.io"]
    resources  = ["ingressclasses"]
  }
  rule {
    verbs          = ["get", "update"]
    api_groups     = [""]
    resources      = ["configmaps"]
    resource_names = ["ingress-controller-leader-nginx"]
  }
  rule {
    verbs      = ["create"]
    api_groups = [""]
    resources  = ["configmaps"]
  }
  rule {
    verbs      = ["get", "update"]
    api_groups = ["coordination.k8s.io"]
    resources  = ["leases"]
    resource_names = ["ingress-controller-leader"]
  }
  rule {
    verbs      = ["create"]
    api_groups = ["coordination.k8s.io"]
    resources  = ["leases"]
  }
  rule {
    verbs      = ["create", "patch"]
    api_groups = [""]
    resources  = ["events"]
  }
  rule {
    verbs      = ["list", "watch", "get"]
    api_groups = ["discovery.k8s.io"]
    resources  = ["endpointslices"]
  }
}

resource "kubernetes_role_binding" "ingress_nginx" {
  metadata {
    name      = "ingress-nginx"
    namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
    labels = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
      "app.kubernetes.io/part-of" = "ingress-nginx"
    }
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.ingress_nginx.metadata[0].name
    namespace = kubernetes_service_account.ingress_nginx.metadata[0].namespace
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.ingress_nginx.metadata[0].name
  }
}

resource "kubernetes_service" "ingress_nginx_controller" {
  metadata {
    name      = "ingress-nginx-controller"
    namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
    labels = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
      "app.kubernetes.io/part-of" = "ingress-nginx"
    }
  }
  spec {
    external_traffic_policy = "Local"
    ip_families = ["IPv4"]
    ip_family_policy = "SingleStack"
    dynamic "port" {
      for_each = local.ports
      content {
        name = port.value["name"]
        protocol = port.value["proto"]
        port = port.value["port"]
        target_port = port.value["name"]
        node_port = port.value["port"]
      }
    }
    selector = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
    }
    type = "NodePort"
  }
}

resource "kubernetes_deployment" "ingress_nginx_controller" {
  metadata {
    name      = "ingress-nginx-controller"
    namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
    labels = {
      "app.kubernetes.io/component" = "controller"
      "app.kubernetes.io/instance" = "ingress-nginx"
      "app.kubernetes.io/name" = "ingress-nginx"
      "app.kubernetes.io/version" = "1.4.0"
      "app.kubernetes.io/part-of" = "ingress-nginx"
    }
  }
  spec {
    selector {
      match_labels = {
        "app.kubernetes.io/component" = "controller"
        "app.kubernetes.io/instance" = "ingress-nginx"
        "app.kubernetes.io/name" = "ingress-nginx"
      }
    }
    template {
      metadata {
        labels = {
          "app.kubernetes.io/component" = "controller"
          "app.kubernetes.io/instance" = "ingress-nginx"
          "app.kubernetes.io/name" = "ingress-nginx"
        }
      }
      spec {
        # volume {
        #   name = "webhook-cert"
        #   secret {
        #     secret_name = "ingress-nginx-admission"
        #   }
        # }
        container {
          name  = "controller"
          image = "registry.k8s.io/ingress-nginx/controller:v1.4.0@sha256:34ee929b111ffc7aa426ffd409af44da48e5a0eea1eb2207994d9e0c0882d143"
          args  = [
            "/nginx-ingress-controller",
            "--publish-service=$(POD_NAMESPACE)/ingress-nginx-controller",
            "--election-id=ingress-controller-leader",
            "--controller-class=k8s.io/ingress-nginx",
            "--ingress-class=nginx",
            "--configmap=$(POD_NAMESPACE)/ingress-nginx-controller",
            # "--validating-webhook=:8443",
            # "--validating-webhook-certificate=/usr/local/certificates/cert",
            # "--validating-webhook-key=/usr/local/certificates/key"
          ]
          dynamic "port" {
            for_each = local.ports
            content {
              name = port.value["name"]
              container_port = port.value["port"]
              protocol = port.value["proto"]
            }
          }
          port {
            name           = "webhook"
            container_port = 8443
            protocol       = "TCP"
          }
          env {
            name = "POD_NAME"
            value_from {
              field_ref {
                field_path = "metadata.name"
              }
            }
          }
          env {
            name = "POD_NAMESPACE"
            value_from {
              field_ref {
                field_path = "metadata.namespace"
              }
            }
          }
          env {
            name  = "LD_PRELOAD"
            value = "/usr/local/lib/libmimalloc.so"
          }
          resources {
            requests = {
              cpu    = "100m"
              memory = "90Mi"
            }
          }
          # volume_mount {
          #   name       = "webhook-cert"
          #   read_only  = true
          #   mount_path = "/usr/local/certificates/"
          # }
          liveness_probe {
            http_get {
              path   = "/healthz"
              port   = "10254"
              scheme = "HTTP"
            }
            initial_delay_seconds = 10
            timeout_seconds       = 1
            period_seconds        = 10
            success_threshold     = 1
            failure_threshold     = 5
          }
          readiness_probe {
            http_get {
              path   = "/healthz"
              port   = "10254"
              scheme = "HTTP"
            }
            initial_delay_seconds = 10
            timeout_seconds       = 1
            period_seconds        = 10
            success_threshold     = 1
            failure_threshold     = 3
          }
          lifecycle {
            pre_stop {
              exec {
                command = ["/wait-shutdown"]
              }
            }
          }
          image_pull_policy = "IfNotPresent"
          security_context {
            capabilities {
              add  = ["NET_BIND_SERVICE"]
              drop = ["ALL"]
            }
            run_as_user                = 101
            allow_privilege_escalation = true
          }
        }
        termination_grace_period_seconds = 300
        dns_policy                       = "ClusterFirst"
        node_selector = {
          "kubernetes.io/os" = "linux"
        }
        service_account_name = kubernetes_service_account.ingress_nginx.metadata[0].name
      }
    }
    min_ready_seconds = 0
    revision_history_limit = 10
  }
}

resource "kubernetes_ingress_class" "nginx" {
  metadata {
    labels = {
      "app.kubernetes.io/component": "controller"
      "app.kubernetes.io/instance": "ingress-nginx"
      "app.kubernetes.io/name": "ingress-nginx"
      "app.kubernetes.io/part-of": "ingress-nginx"
      "app.kubernetes.io/version": "1.4.0"
    }
    name = "nginx"
  }
  spec {
    controller = "k8s.io/ingress-nginx"
  }
}

# # validating webhook might be the cause of 
# #    failed calling webhook "validate.nginx.ingress.kubernetes.io" 
# # ? Not sure, but it was commented before maybe for a good reason
# # -- yup it does indeed break things. Why? What even is a validating webhook configuration?
# 
# resource "kubernetes_service" "ingress_nginx_controller_admission" {
#   metadata {
#     name      = "ingress-nginx-controller-admission"
#     namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
#     labels = {
#       "app.kubernetes.io/component" = "controller"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   spec {
#     port {
#       app_protocol = "https"
#       name        = "https-webhook"
#       port        = 443
#       target_port = "webhook"
#     }
#     selector = {
#       "app.kubernetes.io/component" = "controller"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#     }
#     type = "ClusterIP"
#   }
# }
#
# resource "kubernetes_validating_webhook_configuration" "ingress_nginx_admission" {
#   lifecycle {
#     ignore_changes = [
#       webhook[0].client_config[0].ca_bundle
#     ]
#   }
#   metadata {
#     name = "ingress-nginx-admission"
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   webhook {
#     name = "validate.nginx.ingress.kubernetes.io"
#     client_config {
#       service {
#         namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
#         name      = "ingress-nginx-controller-admission"
#         path      = "/networking/v1/ingresses"
#       }
#     }
#     rule {
#       api_groups = ["networking.k8s.io"]
#       api_versions = ["v1"]
#       operations = ["CREATE", "UPDATE"]
#       resources = ["ingresses"]
#     }
#     failure_policy            = "Fail"
#     match_policy              = "Equivalent"
#     side_effects              = "None"
#     admission_review_versions = ["v1"]
#   }
# }
# 
# resource "kubernetes_service_account" "ingress_nginx_admission" {
#   metadata {
#     name      = "ingress-nginx-admission"
#     namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
# }
# 
# resource "kubernetes_cluster_role" "ingress_nginx_admission" {
#   metadata {
#     name = "ingress-nginx-admission"
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   rule {
#     verbs      = ["get", "update"]
#     api_groups = ["admissionregistration.k8s.io"]
#     resources  = ["validatingwebhookconfigurations"]
#   }
# }
# 
# resource "kubernetes_cluster_role_binding" "ingress_nginx_admission" {
#   metadata {
#     name = "ingress-nginx-admission"
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   subject {
#     kind      = "ServiceAccount"
#     name      = kubernetes_service_account.ingress_nginx_admission.metadata[0].name
#     namespace = kubernetes_service_account.ingress_nginx_admission.metadata[0].namespace
#   }
#   role_ref {
#     api_group = "rbac.authorization.k8s.io"
#     kind      = "ClusterRole"
#     name      = kubernetes_cluster_role.ingress_nginx_admission.metadata[0].name
#   }
# }
# 
# resource "kubernetes_role" "ingress_nginx_admission" {
#   metadata {
#     name      = "ingress-nginx-admission"
#     namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   rule {
#     verbs      = ["get", "create"]
#     api_groups = [""]
#     resources  = ["secrets"]
#   }
# }
# 
# resource "kubernetes_role_binding" "ingress_nginx_admission" {
#   metadata {
#     name      = "ingress-nginx-admission"
#     namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   subject {
#     kind      = "ServiceAccount"
#     name      = kubernetes_service_account.ingress_nginx_admission.metadata[0].name
#     namespace = kubernetes_service_account.ingress_nginx_admission.metadata[0].namespace
#   }
#   role_ref {
#     api_group = "rbac.authorization.k8s.io"
#     kind      = "Role"
#     name      = kubernetes_role.ingress_nginx_admission.metadata[0].name
#   }
# }
# 
# resource "kubernetes_job" "ingress_nginx_admission_create" {
#   metadata {
#     name      = "ingress-nginx-admission-create"
#     namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   spec {
#     template {
#       metadata {
#         name = "ingress-nginx-admission-create"
#         labels = {
#           "app.kubernetes.io/component" = "admission-webhook"
#           "app.kubernetes.io/instance" = "ingress-nginx"
#           "app.kubernetes.io/name" = "ingress-nginx"
#           "app.kubernetes.io/version" = "1.4.0"
#           "app.kubernetes.io/part-of" = "ingress-nginx"
#         }
#       }
#       spec {
#         container {
#           name  = "create"
#           image = "registry.k8s.io/ingress-nginx/kube-webhook-certgen:v20220916-gd32f8c343@sha256:39c5b2e3310dc4264d638ad28d9d1d96c4cbb2b2dcfb52368fe4e3c63f61e10f"
#           args  = [
#             "create", 
#             "--host=ingress-nginx-controller-admission,ingress-nginx-controller-admission.$(POD_NAMESPACE).svc", 
#             "--namespace=$(POD_NAMESPACE)", 
#             "--secret-name=ingress-nginx-admission"
#           ]
#           env {
#             name = "POD_NAMESPACE"
#             value_from {
#               field_ref {
#                 field_path = "metadata.namespace"
#               }
#             }
#           }
#           image_pull_policy = "IfNotPresent"
#           security_context {
#             allow_privilege_escalation = false
#           }
#         }
#         restart_policy       = "OnFailure"
#         service_account_name = kubernetes_service_account.ingress_nginx_admission.metadata[0].name
#         security_context {
#           fs_group = 2000
#           run_as_non_root = true
#           run_as_user =  2000
#         }
#         node_selector = {
#           "kubernetes.io/os" = "linux"
#         }
#       }
#     }
#   }
# }
# 
# resource "kubernetes_job" "ingress_nginx_admission_patch" {
#   metadata {
#     name      = "ingress-nginx-admission-patch"
#     namespace = kubernetes_namespace.ingress_nginx.metadata[0].name
#     labels = {
#       "app.kubernetes.io/component" = "admission-webhook"
#       "app.kubernetes.io/instance" = "ingress-nginx"
#       "app.kubernetes.io/name" = "ingress-nginx"
#       "app.kubernetes.io/version" = "1.4.0"
#       "app.kubernetes.io/part-of" = "ingress-nginx"
#     }
#   }
#   spec {
#     template {
#       metadata {
#         name = "ingress-nginx-admission-patch"
#         labels = {
#           "app.kubernetes.io/component" = "admission-webhook"
#           "app.kubernetes.io/instance" = "ingress-nginx"
#           "app.kubernetes.io/name" = "ingress-nginx"
#           "app.kubernetes.io/version" = "1.4.0"
#           "app.kubernetes.io/part-of" = "ingress-nginx"
#         }
#       }
#       spec {
#         container {
#           name  = "patch"
#           image = "registry.k8s.io/ingress-nginx/kube-webhook-certgen:v20220916-gd32f8c343@sha256:39c5b2e3310dc4264d638ad28d9d1d96c4cbb2b2dcfb52368fe4e3c63f61e10f"
#           args  = [
#             "patch", 
#             "--webhook-name=ingress-nginx-admission", 
#             "--namespace=$(POD_NAMESPACE)", 
#             "--patch-mutating=false", 
#             "--secret-name=ingress-nginx-admission", 
#             "--patch-failure-policy=Fail"
#           ]
#           env {
#             name = "POD_NAMESPACE"
#             value_from {
#               field_ref {
#                 field_path = "metadata.namespace"
#               }
#             }
#           }
#           image_pull_policy = "IfNotPresent"
#           security_context {
#             allow_privilege_escalation = false
#           }
#         }
#         node_selector = {
#           "kubernetes.io/os": "linux"
#         }
#         restart_policy       = "OnFailure"
#         service_account_name = kubernetes_service_account.ingress_nginx_admission.metadata[0].name
#         security_context {
#           run_as_user     = 2000
#           run_as_non_root = true
#           fs_group = 2000
#         }
#       }
#     }
#   }
# }
# 