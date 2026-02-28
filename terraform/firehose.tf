resource "aws_kinesis_firehose_delivery_stream" "s3_delivery" {
  name        = "${var.project_name}-firehose-s3"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.main.arn
    role_arn           = aws_iam_role.firehose_role.arn
  }

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose_role.arn
    bucket_arn = aws_s3_bucket.data_lake.arn
    prefix     = "raw-data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"

    buffering_size     = 5   # MB
    buffering_interval = 300 # seconds (5 min)

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = "/aws/firehose/${var.project_name}"
      log_stream_name = "S3Delivery"
    }
  }
}
