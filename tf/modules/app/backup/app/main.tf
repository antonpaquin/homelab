variable "aws_backup_bucket" {
  type = string
  description = "Where will files be backed up to"
}

variable "backup_secrets" {
  type = object({
    aes-key: string
    hash-salt: string
  })
}

variable "aws_secrets" {
  type = object({
    access_key_id: string
    secret_access_key: string
  })
}

variable "media-pvc" {
  type = string
}

locals {
  namespace = "default"
  # schedule = "${random_integer.cronjob-jitter.result} 0 * * 0"  # Weekly on sunday, a bit after midnight
  schedule = "${random_integer.cronjob-jitter.result} * 31 2 0"  # February 31st aka never
}

resource "random_integer" "cronjob-jitter" {
  min = 0
  max = 59
}

resource "kubernetes_secret" "s3-aws-credentials" {
  metadata {
    name = "namecheap-api-credentials"
    namespace = local.namespace
  }
  data = {
    credentials: <<EOF
[default]
aws_access_key_id = ${var.aws_secrets.access_key_id}
aws_secret_access_key = ${var.aws_secrets.secret_access_key}
EOF
    config: <<EOF
[default]
region = us-west-2
output = json
EOF
  }
}

resource "kubernetes_secret" "backup-crypto-key" {
  metadata {
    name = "backup-crypto-key"
    namespace = local.namespace
  }
  data = {
    AES_KEY = var.backup_secrets.aes-key
    HASH_SALT = var.backup_secrets.hash-salt
  }
}

resource "kubernetes_cron_job_v1" "s3-backup" {
  metadata {
    name = "s3-backup"
    namespace = local.namespace
  }
  spec {
    schedule = local.schedule
    enabled = false
    job_template {
      metadata {}
      spec {
        backoff_limit = 1
        template {
          metadata {}
          spec {
            restart_policy = "Never"
            container {
              name = "main"
              image_pull_policy = "Always"
              image = "docker.io/antonpaquin/misc:hashbak"
              args = [
                "--src-dir", "/media/library",
                "--s3-bucket", var.aws_backup_bucket,
              ]
              env_from {
                secret_ref {
                  name = kubernetes_secret.backup-crypto-key.metadata[0].name
                }
              }
              volume_mount {
                name = "media"
                mount_path = "/media"
              }
              volume_mount {
                name = "aws-creds"
                mount_path = "/root/.aws"
              }
            }
            volume {
              name = "media"
              persistent_volume_claim {
                claim_name = var.media-pvc
              }
            }
            volume {
              name = "aws-creds"
              secret {
                secret_name = kubernetes_secret.s3-aws-credentials.metadata[0].name
              }
            }
          }
        }
      }
    }
  }
}
