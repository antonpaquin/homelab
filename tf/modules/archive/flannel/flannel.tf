locals {
  flannel_namespace = "kube-system"
}

resource "kubernetes_cluster_role" "flannel" {
  metadata {
    name = "flannel"
  }
  # rules:
  rule {
    api_groups = ["extensions"]
    resources = ["podsecuritypolicies"]
    verbs = ["use"]
    resource_names = ["psp.flannel.unprivileged"]
  }
  rule {
    api_groups = [""]
    resources = ["pods"]
    verbs = ["get"]

  }
  rule {
    api_groups = [""]
    resources = ["nodes"]
    verbs = ["list", "watch"]
  }
  rule {
    api_groups = [""]
    resources = ["nodes/status"]
    verbs = ["patch"]
  }
}

resource "kubernetes_service_account" "flannel" {
  metadata {
    name = "flannel"
    namespace = local.flannel_namespace
  }
}

resource "kubernetes_cluster_role_binding" "flannel" {
  metadata {
    name = "flannel"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = kubernetes_cluster_role.flannel.metadata[0].name
  }
  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.flannel.metadata[0].name
    namespace = kubernetes_service_account.flannel.metadata[0].namespace
  }
}

resource "kubernetes_config_map" "flannel" {
  metadata {
    name = "kube-flannel-cfg"
    namespace = local.flannel_namespace
    labels = {
      tier: "node"
      app: "flannel"
    }
  }
  data = {
    "cni-conf.json": <<EOF
{
  "name": "cbr0",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "flannel",
      "delegate": {
        "hairpinMode": true,
        "isDefaultGateway": true
      }
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}
EOF
    "net-conf.json": <<EOF
{
  "Network": "10.244.0.0/16",
  "Backend": {
    "Type": "vxlan"
  }
}
EOF
  }
}

resource "kubernetes_daemonset" "flannel" {
  metadata {
    name = "kube-flannel-ds"
    namespace = local.flannel_namespace
    labels = {
      tier: "node"
      app: "flannel"
    }
  }
  spec {
    selector {
      match_labels = {
        app: "flannel"
      }
    }
    template {
      metadata {
        labels = {
          tier: "node"
          app: "flannel"
        }
      }
      spec {
        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key = "kubernetes.io/os"
                  operator = "In"
                  values = ["linux"]
                }
              }
            }
          }
        }
        host_network =true
        priority_class_name = "system-node-critical"
        toleration {
          operator = "Exists"
          effect = "NoSchedule"
        }
        service_account_name = kubernetes_service_account.flannel.metadata[0].name
        init_container {
          name = "install-cni"
          image = "quay.io/coreos/flannel:v0.14.0"
          command = ["cp"]
          args = ["-f", "/etc/kube-flannel/cni-conf.json", "/etc/cni/net.d/10-flannel.conflist"]
          volume_mount {
            name = "cni"
            mount_path = "/etc/cni/net.d"
          }
          volume_mount {
            name = "flannel-cfg"
            mount_path = "/etc/kube-flannel/"
          }
        }
        container {
          name = "kube-flannel"
          image = "quay.io/coreos/flannel:v0.14.0"
          command = ["/opt/bin/flanneld"]
          args = ["--ip-masq", "--kube-subnet-mgr"]
          resources {
            requests = {
              cpu = "100m"
              memory = "50Mi"
            }
            limits = {
              cpu = "100m"
              memory = "50Mi"
            }
          }
          security_context {
            privileged = false
            capabilities {
              add = ["NET_ADMIN", "NET_RAW"]
            }
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
          volume_mount {
            name = "run"
            mount_path = "/run/flannel"
          }
          volume_mount {
            name = "flannel-cfg"
            mount_path = "/etc/kube-flannel/"
          }
        }
        volume {
          name = "run"
          host_path {
            path = "/run/flannel"
          }
        }
        volume {
          name = "cni"
          host_path {
            path = "/etc/cni/net.d"
          }
        }
        volume {
          name = "flannel-cfg"
          config_map {
            name = "kube-flannel-cfg"
          }
        }
      }
    }
  }
}
