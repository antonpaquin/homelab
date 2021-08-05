resource "kubernetes_config_map" "rook-ceph-init" {
  metadata {
    name = "ceph-pg-health-entrypoint"
    namespace = local.namespace
  }
  # TODO: figure out SSO so I can clear this password stuff
  data = {
    "entrypoint.sh": <<EOF
#! /bin/bash
/usr/local/bin/toolbox.sh --skip-watch
ceph osd crush rule create-replicated replicated_rule_osd default osd
ceph osd pool set device_health_metrics crush_rule replicated_rule_osd

echo 'cirno9ball' > dashboard-pass
ceph dashboard ac-user-set-password admin -i dashboard-pass
rm dashboard-pass
EOF
  }
}

resource "kubernetes_job" "rook-ceph-init" {
  # https://stackoverflow.com/questions/63456581/1-pg-undersized-health-warn-in-rook-ceph-on-single-node-clusterminikube
  metadata {
    name = "rook-ceph-init"
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
            name = kubernetes_config_map.rook-ceph-init.metadata[0].name
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
