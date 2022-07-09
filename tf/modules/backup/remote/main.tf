variable "bucket-name" {
  type = string
}

resource "aws_s3_bucket" "backup" {
  bucket = var.bucket-name
}

resource "aws_iam_user" "s3-full" {
  name = "s3-full"
}

data "aws_iam_policy_document" "s3-full" {
  version = "2012-10-17"
  statement {
    actions = ["s3:*"]
    effect = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_user_policy" "s3-full" {
  policy = data.aws_iam_policy_document.s3-full.json
  user = aws_iam_user.s3-full.name
}

resource "aws_iam_access_key" "s3-full" {
  user = aws_iam_user.s3-full.name
}

output "s3-full-key-id" {
  value = aws_iam_access_key.s3-full.id
}

output "s3-full-key-secret" {
  value = aws_iam_access_key.s3-full.secret
}

