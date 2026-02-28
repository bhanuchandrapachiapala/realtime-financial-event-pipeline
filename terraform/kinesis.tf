resource "aws_kinesis_stream" "main" {
  name             = "${var.project_name}-stream"
  shard_count      = 1
  retention_period = 24

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Name = "${var.project_name}-stream"
  }
}
