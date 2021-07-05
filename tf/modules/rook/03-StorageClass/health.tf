resource "kubernetes_config_map" "pg-health-entrypoint" {
  metadata {
    name = "ceph-pg-health-entrypoint"
    namespace = local.namespace
  }
  data = {
    "entrypoint.sh": <<EOF
#! /bin/bash
/usr/local/bin/toolbox.sh --skip-watch
ceph osd crush rule create-replicated replicated_rule_osd default osd
ceph osd pool set device_health_metrics crush_rule replicated_rule_osd
EOF
  }
}

resource "kubernetes_job" "pg-health" {
  # https://stackoverflow.com/questions/63456581/1-pg-undersized-health-warn-in-rook-ceph-on-single-node-clusterminikube
  metadata {
    name = "ceph-pg-health"
    namespace = local.namespace
  }
  spec {
    template {
      metadata {}
      spec {
        dns_policy = "ClusterFirstWithHostNet"
        container {
          name = "rook-ceph-tools"
          image = "rook/ceph:v1.6.5"
          command = ["/entrypoints/entrypoint.sh"]
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
            name = "ceph-config"
            mount_path = "/etc/ceph"
          }
          volume_mount {
            name = "mon-endpoint-volume"
            mount_path = "/etc/rook"
          }
          volume_mount {
            name = "entrypoints"
            mount_path = "/entrypoints"
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
        volume {
          name = "entrypoints"
          config_map {
            name = kubernetes_config_map.pg-health-entrypoint.metadata[0].name
            items {
              key = "entrypoint.sh"
              path = "entrypoint.sh"
              mode = "0777"
            }
          }
        }
      }
    }
  }
}
