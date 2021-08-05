resource "kubernetes_secret" "ceph-provisioner-secret" {
  metadata {
    name = "ceph-provisioner-secret"
    namespace = local.namespace
  }
  data = {
    userID = "admin"
    userKey = local.secret["ceph"]["admin-secret"]
  }
  type = "kubernetes.io/rbd"
}

# I kubectl cp'd ceph.conf to the nodeplugin csi-rbdplugin container and am now getting No such process
# Progress, I think
# But this is damn impossible to google
# Perhaps: rook, dump yaml, port?

resource "helm_release" "ceph-csi-rbd" {
  repository = "https://ceph.github.io/csi-charts"
  chart = "ceph-csi-rbd"
  name = "ceph-csi-rbd"
  namespace = local.namespace
  version = "1.3.0-canary"

  values = [yamlencode({
    csiConfig: [{
      clusterID: local.cluster_name
      monitors: local.mon_list
    }]
    provisioner: {
      defaultFSType: "xfs"
      replicaCount: 1
    }
    storageClass: {
      create: false
      name: kubernetes_storage_class.ceph.metadata[0].name
    }
    secret: {
      name: kubernetes_secret.ceph-provisioner-secret.metadata[0].name
      userID: "client.admin"
      userKey: local.secret["ceph"]["admin-secret"]
    }
  })]
}

resource "kubernetes_storage_class" "ceph" {
  storage_provisioner = "rbd.csi.ceph.com"
  metadata {
    name = "ceph-block"
    annotations = {
      "storageclass.kubernetes.io/is-default-class": "true"
    }
  }
  parameters = {
    clusterID: local.cluster_name
    pool: local.pools.rbd0-meta.name
    # dataPool: local.pools.rbd0.name
    imageFormat: "2"
    imageFeatures: "layering"
    "csi.storage.k8s.io/provisioner-secret-name": kubernetes_secret.ceph-provisioner-secret.metadata[0].name
    "csi.storage.k8s.io/provisioner-secret-namespace": kubernetes_secret.ceph-provisioner-secret.metadata[0].namespace
    "csi.storage.k8s.io/controller-expand-secret-name": kubernetes_secret.ceph-provisioner-secret.metadata[0].name
    "csi.storage.k8s.io/controller-expand-secret-namespace": kubernetes_secret.ceph-provisioner-secret.metadata[0].namespace
    "csi.storage.k8s.io/node-stage-secret-name": kubernetes_secret.ceph-provisioner-secret.metadata[0].name
    "csi.storage.k8s.io/node-stage-secret-namespace": kubernetes_secret.ceph-provisioner-secret.metadata[0].namespace
    "csi.storage.k8s.io/fstype": "xfs"
  }
  reclaim_policy = "Delete"
}

