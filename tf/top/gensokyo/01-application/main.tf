locals {
  secret = yamldecode(file("../../secret.yaml"))
  domain = "antonpaqu.in"

  cluster = {
    reimu = {
      local-ip-address = "192.168.1.103"
    }
    hakurei = {
      local-ip-address = "192.168.1.108"
    }
    reimu-00 = {
      local-ip-address = "192.168.1.105"
    }
  }

  aws_backup_bucket = "antonpaquin-backup"

  tls_secrets = {
    default: {name: "tls-cert", namespace: "default"}
  }
}
