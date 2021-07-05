# Apply this in order to restore an existing cluster when kubernetes goes down... hopefully

data "local_file" "secret" {
  filename = "../../../secret.yaml"
}

locals {
  secret = yamldecode(data.local_file.secret.content)
}

resource "kubernetes_secret" "rook_ceph_mon" {
  metadata {
    name      = "rook-ceph-mon"
    namespace = "rook"
  }
  data = {
    ceph-username = "client.admin"
    fsid = "431160f4-af59-4ab0-af63-3c53e020aee0"

    ceph-secret = local.secret["rook"]["ceph-secret"]
    mon-secret = local.secret["rook"]["mon-secret"]
  }
  type = "kubernetes.io/rook"
}

resource "kubernetes_secret" "rook_ceph_mons_keyring" {
  metadata {
    name      = "rook-ceph-mons-keyring"
    namespace = "rook"
  }
  data = {
    keyring = <<EOF
[mon.]
	key = ${local.secret["rook"]["mon-secret"]}
	caps mon = "allow *"


[client.admin]
	key = ${local.secret["rook"]["ceph-secret"]}
	caps mds = "allow *"
	caps mon = "allow *"
	caps osd = "allow *"
	caps mgr = "allow *"
EOF
  }
  type = "kubernetes.io/rook"
}

resource "kubernetes_secret" "rook_ceph_admin_keyring" {
  metadata {
    name      = "rook-ceph-admin-keyring"
    namespace = "rook"
  }

  data = {
    keyring = <<EOF
[client.admin]
	key = ${local.secret["rook"]["ceph-secret"]}
	caps mds = "allow *"
	caps mon = "allow *"
	caps osd = "allow *"
	caps mgr = "allow *"
EOF
  }

  type = "kubernetes.io/rook"
}

resource "kubernetes_service" "rook_ceph_mon_a" {
  metadata {
    name      = "rook-ceph-mon-a"
    namespace = "rook"

    labels = {
      app = "rook-ceph-mon"
      ceph_daemon_id = "a"
      ceph_daemon_type = "mon"
      mon = "a"
      mon_cluster = "rook"
      rook_cluster = "rook"
    }
  }

  spec {
    port {
      name        = "tcp-msgr1"
      protocol    = "TCP"
      port        = 6789
      target_port = "6789"
    }

    port {
      name        = "tcp-msgr2"
      protocol    = "TCP"
      port        = 3300
      target_port = "3300"
    }

    selector = {
      app = "rook-ceph-mon"
      ceph_daemon_id = "a"
      mon = "a"
      mon_cluster = "rook"
      rook_cluster = "rook"
    }

    type             = "ClusterIP"
    session_affinity = "None"
  }
}

resource "kubernetes_service" "rook_ceph_mon_b" {
  metadata {
    name      = "rook-ceph-mon-b"
    namespace = "rook"

    labels = {
      app = "rook-ceph-mon"
      ceph_daemon_id = "b"
      ceph_daemon_type = "mon"
      mon = "b"
      mon_cluster = "rook"
      rook_cluster = "rook"
    }
  }

  spec {
    port {
      name        = "tcp-msgr1"
      protocol    = "TCP"
      port        = 6789
      target_port = "6789"
    }

    port {
      name        = "tcp-msgr2"
      protocol    = "TCP"
      port        = 3300
      target_port = "3300"
    }

    selector = {
      app = "rook-ceph-mon"
      ceph_daemon_id = "b"
      mon = "b"
      mon_cluster = "rook"
      rook_cluster = "rook"
    }

    type             = "ClusterIP"
    session_affinity = "None"
  }
}

resource "kubernetes_service" "rook_ceph_mon_c" {
  metadata {
    name      = "rook-ceph-mon-c"
    namespace = "rook"

    labels = {
      app = "rook-ceph-mon"
      ceph_daemon_id = "c"
      ceph_daemon_type = "mon"
      mon = "c"
      mon_cluster = "rook"
      rook_cluster = "rook"
    }
  }

  spec {
    port {
      name        = "tcp-msgr1"
      protocol    = "TCP"
      port        = 6789
      target_port = "6789"
    }

    port {
      name        = "tcp-msgr2"
      protocol    = "TCP"
      port        = 3300
      target_port = "3300"
    }

    selector = {
      app = "rook-ceph-mon"
      ceph_daemon_id = "c"
      mon = "c"
      mon_cluster = "rook"
      rook_cluster = "rook"
    }

    type             = "ClusterIP"
    session_affinity = "None"
  }
}



locals {
  mon-a-ip = kubernetes_service.rook_ceph_mon_a.spec[0].cluster_ip
  mon-b-ip = kubernetes_service.rook_ceph_mon_b.spec[0].cluster_ip
  mon-c-ip = kubernetes_service.rook_ceph_mon_b.spec[0].cluster_ip
}

resource "kubernetes_config_map" "rook_ceph_mon_endpoints" {
  metadata {
    name      = "rook-ceph-mon-endpoints"
    namespace = "rook"
  }

  data = {
    csi-cluster-config-json = jsonencode([{
      clusterID: "rook",
      monitors: [
        "${local.mon-a-ip}:6789",
        "${local.mon-b-ip}:6789",
        "${local.mon-c-ip}:6789",
      ]
    }])

    data = join(",", [
      "a=${local.mon-a-ip}:6789",
      "b=${local.mon-b-ip}:6789",
      "c=${local.mon-c-ip}:6789",
    ])

    mapping = jsonencode({
      node: {
        a: {
          Name: "reimu-00"
          Hostname: "reimu-00"
          Address: "10.0.4.64"
        },
        b: {
          Name: "reimu-00"
          Hostname: "reimu-00"
          Address: "10.0.4.64"
        }
        c: {
          Name: "reimu-00"
          Hostname: "reimu-00"
          Address: "10.0.4.64"
        }
      }
    })

    maxMonId = "2"
  }
}

