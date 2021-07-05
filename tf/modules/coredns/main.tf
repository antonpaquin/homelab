# Yes, kubeadm installs coredns, but for some reason that doesn't work
# This is from https://github.com/coredns/deployment

locals {
  namespace = "kube-system"
}

# resource "kubernetes_service_account" "coredns" {
#   metadata {
#     name      = "coredns"
#     namespace = local.namespace
#   }
# }
locals {
  service_account_name = "coredns"
}

resource "kubernetes_cluster_role" "system_coredns" {
  metadata {
    name = "system:coredns"
    labels = {
      "kubernetes.io/bootstrapping" = "rbac-defaults"
    }
  }
  rule {
    verbs      = ["list", "watch"]
    api_groups = [""]
    resources  = ["endpoints", "services", "pods", "namespaces"]
  }
  rule {
    verbs      = ["list", "watch"]
    api_groups = ["discovery.k8s.io"]
    resources  = ["endpointslices"]
  }
}

resource "kubernetes_cluster_role_binding" "system_coredns" {
  metadata {
    name = "system:coredns"
    labels = {
      "kubernetes.io/bootstrapping" = "rbac-defaults"
    }
    annotations = {
      "rbac.authorization.kubernetes.io/autoupdate" = "true"
    }
  }
  subject {
    kind      = "ServiceAccount"
    name      = local.service_account_name
    namespace = local.namespace
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.system_coredns.metadata[0].name
  }
}

resource "kubernetes_config_map" "coredns" {
  metadata {
    name      = "coredns"
    namespace = local.namespace
  }
  data = {
    Corefile = <<EOF
.:53 {
    errors
    health {
      lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
      fallthrough in-addr.arpa ip6.arpa
    }
    prometheus :9153
    forward . /etc/resolv.conf {
      max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
EOF
  }
}

resource "kubernetes_deployment" "coredns" {
  metadata {
    name      = "coredns"
    namespace = local.namespace
    labels = {
      k8s-app = "kube-dns"
      "kubernetes.io/name" = "CoreDNS"
    }
  }
  spec {
    selector {
      match_labels = {
        k8s-app = "kube-dns"
      }
    }
    template {
      metadata {
        labels = {
          k8s-app = "kube-dns"
        }
      }
      spec {
        volume {
          name = "config-volume"
          config_map {
            name = kubernetes_config_map.coredns.metadata[0].name
            items {
              key  = "Corefile"
              path = "Corefile"
            }
          }
        }
        container {
          name  = "coredns"
          image = "coredns/coredns:1.8.3"
          args  = ["-conf", "/etc/coredns/Corefile"]
          port {
            name           = "dns"
            container_port = 53
            protocol       = "UDP"
          }
          port {
            name           = "dns-tcp"
            container_port = 53
            protocol       = "TCP"
          }
          port {
            name           = "metrics"
            container_port = 9153
            protocol       = "TCP"
          }
          resources {
            limits = {
              memory = "170Mi"
            }
            requests = {
              cpu    = "100m"
              memory = "70Mi"
            }
          }
          volume_mount {
            name       = "config-volume"
            read_only  = true
            mount_path = "/etc/coredns"
          }
          liveness_probe {
            http_get {
              path   = "/health"
              port   = "8080"
              scheme = "HTTP"
            }
            initial_delay_seconds = 60
            timeout_seconds       = 5
            success_threshold     = 1
            failure_threshold     = 5
          }
          readiness_probe {
            http_get {
              path   = "/ready"
              port   = "8181"
              scheme = "HTTP"
            }
          }
          image_pull_policy = "IfNotPresent"
          security_context {
            capabilities {
              add  = ["NET_BIND_SERVICE"]
              drop = ["all"]
            }
            read_only_root_filesystem = true
          }
        }
        dns_policy = "Default"
        node_selector = {
          "kubernetes.io/os" = "linux"
        }
        service_account_name = local.service_account_name
        affinity {
          pod_anti_affinity {
            preferred_during_scheduling_ignored_during_execution {
              weight = 100
              pod_affinity_term {
                label_selector {}
                topology_key = "kubernetes.io/hostname"
              }
            }
          }
        }
        toleration {
          key      = "CriticalAddonsOnly"
          operator = "Exists"
        }
        priority_class_name = "system-cluster-critical"
      }
    }
    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_unavailable = "1"
      }
    }
  }
}

resource "kubernetes_service" "kube_dns" {
  metadata {
    name      = "kube-dns"
    namespace = local.namespace
    labels = {
      k8s-app = "kube-dns"
      "kubernetes.io/cluster-service" = "true"
      "kubernetes.io/name" = "CoreDNS"
    }
    annotations = {
      "prometheus.io/port" = "9153"
      "prometheus.io/scrape" = "true"
    }
  }
  spec {
    port {
      name     = "dns"
      protocol = "UDP"
      port     = 53
    }
    port {
      name     = "dns-tcp"
      protocol = "TCP"
      port     = 53
    }
    port {
      name     = "metrics"
      protocol = "TCP"
      port     = 9153
    }
    selector = {
      k8s-app = "kube-dns"
    }
    cluster_ip = "10.96.0.10"
  }
}

