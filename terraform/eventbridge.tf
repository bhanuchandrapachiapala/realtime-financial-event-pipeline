resource "aws_scheduler_schedule" "data_ingestion" {
  name       = "${var.project_name}-ingest-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  # Run every 60 seconds
  schedule_expression = "rate(1 minutes)"

  target {
    arn      = aws_lambda_function.data_ingester.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# Allow EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_ingester.function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.data_ingestion.arn
}
