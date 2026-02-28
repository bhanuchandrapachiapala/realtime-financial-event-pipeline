resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Invocations"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.data_ingester.function_name],
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.price_processor.function_name],
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.anomaly_detector.function_name],
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.aggregator.function_name]
          ]
          period = 60
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Lambda Errors"
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.data_ingester.function_name],
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.price_processor.function_name],
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.anomaly_detector.function_name]
          ]
          period = 60
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Kinesis - Incoming Records"
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", "StreamName", aws_kinesis_stream.main.name]
          ]
          period = 60
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "DynamoDB - Write Capacity"
          metrics = [
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", aws_dynamodb_table.live_prices.name],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", aws_dynamodb_table.anomalies.name]
          ]
          period = 60
          stat   = "Sum"
        }
      }
    ]
  })
}

# Alarm: Lambda errors > 5 in 5 minutes
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda errors exceeded threshold"
  alarm_actions       = [aws_sns_topic.anomaly_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.data_ingester.function_name
  }
}
