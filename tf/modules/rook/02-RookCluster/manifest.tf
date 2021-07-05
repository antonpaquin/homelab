# Terraform gets buggy when this is in the state so I'm keeping it out unless I need it
# "kubernetes-alpha" being alpha, I guess

resource "kubernetes_manifest" "rook-cluster" {
  depends_on = [module.prep_storage, module.prep_meta]
  provider = kubernetes-alpha
  manifest = {
    apiVersion: "ceph.rook.io/v1"
    kind: "CephCluster"
    metadata: {
      name: "rook-ceph"
      namespace: local.namespace
    }
    spec = {
      cephVersion = {
        image: "ceph/ceph:v16.2.4"
        allowUnsupported: false
      }
      dataDirHostPath: "/storage/meta"
      skipUpgradeChecks: false
      continueUpgradeAfterChecksEvenIfNotHealthy: false
      waitTimeoutForHealthyOSDInMinutes: 10
      mon: {
        count: 3
        allowMultiplePerNode: true
      }
      mgr: {
        count: 1
        modules: [
          {
            name: "pg_autoscaler"
            enabled: true
          }
        ]
      }
      dashboard: {
        enabled: true
      }
      monitoring: {
        enabled: false
      }
      crashCollector: {
        disable: false
        daysToRetain: 30
      }
      cleanupPolicy: {
        confirmation: ""
        sanitizeDisks: {
          method: "quick"
          dataSource: "zero"
          iteration: 1
        }
        allowUninstallWithVolumes: false
      }
      placement: {}
      annotations: {}
      labels: {}
      resources: {
        mgr: {
          limits: {
            cpu: "500m"
            memory: "1024Mi"
          }
          requests: {
            cpu: "500m"
            memory: "1024Mi"
          }
        }
      }
      removeOSDsIfOutAndSafeToRemove: false
      storage: {
        useAllNodes: false
        useAllDevices: false
        config: {}
        storageClassDeviceSets: [
        for key, value in local.storage :
        {
          name: key
          count: 1
          portable: false
          tuneDeviceClass: true
          volumeClaimTemplates: [
            {
              metadata: {
                name: kubernetes_persistent_volume.physical_pv[key].metadata[0].name
              }
              spec: {
                resources: {
                  requests: {
                    storage: value.capacity
                  }
                }
                storageClassName: kubernetes_storage_class.physical.metadata[0].name
                volumeMode: "Block"
                accessModes: ["ReadWriteOnce"]
              }
            }
          ]
        }
        ]
      }
      disruptionManagement: {
        managePodBudgets: true
        osdMaintenanceTimeout: 30
        pgHealthCheckTimeout: 0
        manageMachineDisruptionBudgets: false
        machineDisruptionBudgetNamespace: "openshift-machine-api"
      }
      healthCheck: {
        daemonHealth: {
          mon: {disabled: false, interval: "45s"}
          osd: {disabled: false, interval: "60s"}
          status: {disabled: false, interval: "60s"}
        }
        livenessProbe: {
          mon: {disabled: false}
          mgr: {disabled: false}
          osd: {disabled: false}
        }
      }
    }
  }
}

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
