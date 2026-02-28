resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-data-lake-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-data-lake"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake_lifecycle" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket" "lambda_packages" {
  bucket = "${var.project_name}-lambda-packages-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}
