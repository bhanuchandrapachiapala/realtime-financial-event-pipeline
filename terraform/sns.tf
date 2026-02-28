resource "aws_sns_topic" "anomaly_alerts" {
  name = "${var.project_name}-anomaly-alerts"
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.anomaly_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
