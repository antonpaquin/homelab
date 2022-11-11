locals {
  secret = yamldecode(file("../../secret.yaml"))
  domain = "antonpaqu.in"

  cluster = {
    reimu = {
      local-ip-address = "192.168.0.102"
    }
    hakurei = {
      local-ip-address = "192.168.0.103"
    }
    reimu-00 = {
      local-ip-address = "192.168.0.104"
    }
  }

  aws_backup_bucket = "antonpaquin-backup"

  tls_secrets = {
    default: {name: "tls-cert", namespace: "default"}
    rook: {name: "tls-cert", namespace: "rook"}
  }
}
