variable "reimu-ingress-ip" {
  type = string
}

locals {
  namespace = "default"
}

resource "kubernetes_service" "bind9" {
  metadata {
    name = "bind9"
    namespace = local.namespace
  }
  spec {
    type = "NodePort"
    selector = {
      app = "bind9"
    }
    port {
      port = 53
      target_port = 53
      node_port = 53
      protocol = "UDP"
    }
  }
}

resource "kubernetes_deployment" "bind9" {
  wait_for_rollout = false
  metadata {
    name = "bind9"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "bind9"
      }
    }
    template {
      metadata {
        labels = {
          app = "bind9"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/resystit/bind9"
          volume_mount {
            name = "config"
            mount_path = "/etc/bind"
          }
        }
        volume {
          name = "config"
          config_map {
            name = "bind9"
          }
        }
      }
    }
  }
}

resource "kubernetes_config_map" "bind9" {
  metadata {
    name = "bind9"
    namespace = local.namespace
  }
  data = {
    "named.conf" = <<EOF
options {
        directory "/var/bind";

        listen-on { 0.0.0.0/0; };
        allow-query { 0.0.0.0/0; };

        listen-on-v6 { none; };
        allow-transfer { none; };

        forwarders {
            1.1.1.1;
            1.0.0.1;
        };

        pid-file "/var/run/named/named.pid";

        allow-recursion { any; };
        recursion yes;
};

zone "k8s.local"   {
        type master;
        file "/etc/bind/k8s.local";
        allow-query { any; };
};

zone "antonpaqu.in" {
        type master;
        file "/etc/bind/k8s.local";
        allow-query { any; };
};

EOF
    "k8s.local" = <<EOF
$TTL    604800
@       IN      SOA     localhost. root.localhost. (
                              6         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
;

@       IN      NS      localhost. ;
@       IN      A       ${var.reimu-ingress-ip} ;
*       IN      A       ${var.reimu-ingress-ip} ;
EOF
  }
}