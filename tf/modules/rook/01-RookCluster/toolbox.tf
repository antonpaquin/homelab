resource "kubernetes_deployment" "toolbox" {
  metadata {
    name = "rook-ceph-tools"
    namespace = local.namespace
    labels = {
      app: "rook-ceph-tools"
    }
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app: "rook-ceph-tools"
      }
    }
    template {
      metadata {
        labels = {
          app: "rook-ceph-tools"
        }
      }
      spec {
        dns_policy = "ClusterFirstWithHostNet"
        container {
          name = "rook-ceph-tools"
          image = "rook/ceph:v1.6.5"
          command = ["/tini"]
          args = ["-g", "--", "/usr/local/bin/toolbox.sh"]
          image_pull_policy = "IfNotPresent"
          env {
            name = "ROOK_CEPH_USERNAME"
            value_from {
              secret_key_ref {
                name = "rook-ceph-mon"
                key = "ceph-username"
              }
            }
          }
          env {
            name = "ROOK_CEPH_SECRET"
            value_from {
              secret_key_ref {
                name = "rook-ceph-mon"
                key = "ceph-secret"
              }
            }
          }
          volume_mount {
            mount_path = "/etc/ceph"
            name = "ceph-config"
          }
          volume_mount {
            mount_path = "/etc/rook"
            name = "mon-endpoint-volume"
          }
        }
        volume {
          name = "mon-endpoint-volume"
          config_map {
            name = "rook-ceph-mon-endpoints"
            items {
              key = "data"
              path = "mon-endpoints"
            }
          }
        }
        volume {
          name = "ceph-config"
          empty_dir {}
        }
      }
    }
  }
}
