output "api_endpoint" {
  value       = aws_apigatewayv2_api.main.api_endpoint
  description = "API Gateway endpoint URL"
}

output "kinesis_stream_name" {
  value = aws_kinesis_stream.main.name
}

output "data_lake_bucket" {
  value = aws_s3_bucket.data_lake.id
}

output "cloudwatch_dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "sns_topic_arn" {
  value = aws_sns_topic.anomaly_alerts.arn
}
