module "await-csi-configmap" {
  source = "../../../modules/kubernetes_waiter"
  kind = "configmap"
  name = "rook-ceph-csi-config"
  namespace = "rook-ceph"
}

data "kubernetes_config_map" "csi-config" {
  depends_on = [module.await-csi-configmap]
  metadata {
    name = "rook-ceph-csi-config"
    namespace = "rook-ceph"
  }
}

locals {
  csi_config_json = jsondecode(data.kubernetes_config_map.csi-config.data["csi-cluster-config-json"])[0]
  cluster_uid = local.csi_config_json["clusterID"]
}

resource "kubernetes_storage_class" "ceph" {
  storage_provisioner = "${local.namespace}.rbd.csi.ceph.com"
  metadata {
    name = "ceph-block"
    annotations = {
      "storageclass.kubernetes.io/is-default-class": "true"
    }
  }
  parameters = {
    clusterID: local.cluster_uid
    pool: kubernetes_manifest.rook-blockpool-meta.manifest.metadata.name
    dataPool: kubernetes_manifest.rook-blockpool.manifest.metadata.name
    imageFormat: "2"
    imageFeatures: "layering"
    "csi.storage.k8s.io/provisioner-secret-name": "rook-csi-rbd-provisioner"
    "csi.storage.k8s.io/provisioner-secret-namespace": "rook-ceph"
    "csi.storage.k8s.io/controller-expand-secret-name": "rook-csi-rbd-provisioner"
    "csi.storage.k8s.io/controller-expand-secret-namespace": "rook-ceph"
    "csi.storage.k8s.io/node-stage-secret-name": "rook-csi-rbd-node"
    "csi.storage.k8s.io/node-stage-secret-namespace": "rook-ceph"
    "csi.storage.k8s.io/fstype": "xfs"
  }
  reclaim_policy = "Delete"
}
