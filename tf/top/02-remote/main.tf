module "backup-s3" {
  source = "../../modules/backup/remote"
  bucket-name = "antonpaquin-backup"
}