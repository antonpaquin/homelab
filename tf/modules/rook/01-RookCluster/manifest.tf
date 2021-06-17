# Terraform gets buggy when this is in the state so I'm keeping it out unless I need it
# "kubernetes-alpha" being alpha, I guess

# resource "kubernetes_manifest" "rook-cluster" {
#   depends_on = [module.prep_storage, module.prep_meta]
#   provider = kubernetes-alpha
#   manifest = {
#     apiVersion: "ceph.rook.io/v1"
#     kind: "CephCluster"
#     metadata: {
#       name: "rook-ceph"
#       namespace: local.namespace
#     }
#     spec = {
#       cephVersion = {
#         image: "ceph/ceph:v16.2.4"
#         allowUnsupported: false
#       }
#       dataDirHostPath: "/storage/meta"
#       skipUpgradeChecks: false
#       continueUpgradeAfterChecksEvenIfNotHealthy: false
#       waitTimeoutForHealthyOSDInMinutes: 10
#       mon: {
#         count: 3
#         allowMultiplePerNode: true
#       }
#       mgr: {
#         count: 1
#         modules: [
#           {
#             name: "pg_autoscaler"
#             enabled: true
#           }
#         ]
#       }
#       dashboard: {
#         enabled: true
#       }
#       monitoring: {
#         enabled: false
#       }
#       crashCollector: {
#         disable: false
#         daysToRetain: 30
#       }
#       cleanupPolicy: {
#         confirmation: ""
#         sanitizeDisks: {
#           method: "quick"
#           dataSource: "zero"
#           iteration: 1
#         }
#         allowUninstallWithVolumes: false
#       }
#       placement: {}
#       annotations: {}
#       labels: {}
#       resources: {
#         mgr: {
#           limits: {
#             cpu: "500m"
#             memory: "1024Mi"
#           }
#           requests: {
#             cpu: "500m"
#             memory: "1024Mi"
#           }
#         }
#       }
#       removeOSDsIfOutAndSafeToRemove: false
#       storage: {
#         useAllNodes: false
#         useAllDevices: false
#         config: {}
#         storageClassDeviceSets: [
#         for key, value in local.storage :
#         {
#           name: key
#           count: 1
#           portable: false
#           tuneDeviceClass: true
#           volumeClaimTemplates: [
#             {
#               metadata: {
#                 name: kubernetes_persistent_volume.physical_pv[key].metadata[0].name
#               }
#               spec: {
#                 resources: {
#                   requests: {
#                     storage: value.capacity
#                   }
#                 }
#                 storageClassName: kubernetes_storage_class.physical.metadata[0].name
#                 volumeMode: "Block"
#                 accessModes: ["ReadWriteOnce"]
#               }
#             }
#           ]
#         }
#         ]
#       }
#       disruptionManagement: {
#         managePodBudgets: true
#         osdMaintenanceTimeout: 30
#         pgHealthCheckTimeout: 0
#         manageMachineDisruptionBudgets: false
#         machineDisruptionBudgetNamespace: "openshift-machine-api"
#       }
#       healthCheck: {
#         daemonHealth: {
#           mon: {disabled: false, interval: "45s"}
#           osd: {disabled: false, interval: "60s"}
#           status: {disabled: false, interval: "60s"}
#         }
#         livenessProbe: {
#           mon: {disabled: false}
#           mgr: {disabled: false}
#           osd: {disabled: false}
#         }
#       }
#     }
#   }
# }

resource "kubernetes_manifest" "rook-blockpool" {
  provider = kubernetes-alpha
  lifecycle {prevent_destroy = true}
  manifest = {
    apiVersion: "ceph.rook.io/v1"
    kind: "CephBlockPool"
    metadata: {
      name: "rbd0"
      namespace: local.namespace
    }
    spec: {
      failureDomain: "osd"
      erasureCoded: {
        dataChunks: 2
        codingChunks: 1
      }
    }
  }
}

resource "kubernetes_manifest" "rook-blockpool-meta" {
  provider = kubernetes-alpha
  lifecycle {prevent_destroy = true}
  manifest = {
    apiVersion: "ceph.rook.io/v1"
    kind: "CephBlockPool"
    metadata: {
      name: "rbd0-meta"
      namespace: local.namespace
    }
    spec: {
      failureDomain: "osd"
      replicated: {
        size: 3
      }
    }
  }
}

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
