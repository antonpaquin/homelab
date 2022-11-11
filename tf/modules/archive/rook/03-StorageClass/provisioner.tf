module "await-csi-configmap" {
  source = "../../../modules/kubernetes_waiter"
  kind = "configmap"
  name = "rook-ceph-csi-config"
  namespace = local.namespace
}

data "kubernetes_config_map" "csi-config" {
  depends_on = [module.await-csi-configmap]
  metadata {
    name = "rook-ceph-csi-config"
    namespace = local.namespace
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
    pool: local.metaPoolName
    dataPool: local.dataPoolName
    imageFormat: "2"
    imageFeatures: "layering"
    "csi.storage.k8s.io/provisioner-secret-name": "rook-csi-rbd-provisioner"
    "csi.storage.k8s.io/provisioner-secret-namespace": local.namespace
    "csi.storage.k8s.io/controller-expand-secret-name": "rook-csi-rbd-provisioner"
    "csi.storage.k8s.io/controller-expand-secret-namespace": local.namespace
    "csi.storage.k8s.io/node-stage-secret-name": "rook-csi-rbd-node"
    "csi.storage.k8s.io/node-stage-secret-namespace": local.namespace
    "csi.storage.k8s.io/fstype": "xfs"
  }
  reclaim_policy = "Delete"
}

resource "kubernetes_storage_class" "name" {
  storage_provisioner = "${local.namespace}.cephfs.csi.ceph.com"
  metadata {
    name = "ceph-cephfs"
  }
  parameters = {
    clusterID: local.cluster_uid
    fsName: local.cephfsName
    pool: "${local.cephfsName}-data0"
    "csi.storage.k8s.io/provisioner-secret-name": "rook-csi-cephfs-provisioner"
    "csi.storage.k8s.io/provisioner-secret-namespace": local.namespace
    "csi.storage.k8s.io/controller-expand-secret-name": "rook-csi-cephfs-provisioner"
    "csi.storage.k8s.io/controller-expand-secret-namespace": local.namespace
    "csi.storage.k8s.io/node-stage-secret-name": "rook-csi-cephfs-node"
    "csi.storage.k8s.io/node-stage-secret-namespace": local.namespace
  }
}
