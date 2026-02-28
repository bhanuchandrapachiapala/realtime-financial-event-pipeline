# ── Data Ingester Lambda ──────────────────────────
resource "aws_lambda_function" "data_ingester" {
  function_name = "${var.project_name}-data-ingester"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 128

  filename         = "${path.module}/../lambdas/data_ingester/package.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/data_ingester/package.zip")

  environment {
    variables = {
      KINESIS_STREAM_NAME   = aws_kinesis_stream.main.name
      ALPHA_VANTAGE_API_KEY = var.alpha_vantage_api_key
    }
  }
}

# ── Price Processor Lambda ─────────────────────────
resource "aws_lambda_function" "price_processor" {
  function_name = "${var.project_name}-price-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 128

  filename         = "${path.module}/../lambdas/price_processor/package.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/price_processor/package.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.live_prices.name
    }
  }
}

# Kinesis trigger for price_processor
resource "aws_lambda_event_source_mapping" "price_processor_trigger" {
  event_source_arn  = aws_kinesis_stream.main.arn
  function_name     = aws_lambda_function.price_processor.arn
  starting_position = "LATEST"
  batch_size        = 10

  # Process even if some records fail
  bisect_batch_on_function_error = true
  maximum_retry_attempts         = 3
}

# ── Anomaly Detector Lambda ────────────────────────
resource "aws_lambda_function" "anomaly_detector" {
  function_name = "${var.project_name}-anomaly-detector"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 256

  filename         = "${path.module}/../lambdas/anomaly_detector/package.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/anomaly_detector/package.zip")

  environment {
    variables = {
      DYNAMODB_TABLE   = aws_dynamodb_table.live_prices.name
      ANOMALY_TABLE    = aws_dynamodb_table.anomalies.name
      SNS_TOPIC_ARN    = aws_sns_topic.anomaly_alerts.arn
      Z_SCORE_THRESHOLD = "2.5"
    }
  }
}

resource "aws_lambda_event_source_mapping" "anomaly_detector_trigger" {
  event_source_arn  = aws_kinesis_stream.main.arn
  function_name     = aws_lambda_function.anomaly_detector.arn
  starting_position = "LATEST"
  batch_size        = 10

  bisect_batch_on_function_error = true
  maximum_retry_attempts         = 3
}

# ── Aggregator Lambda ──────────────────────────────
resource "aws_lambda_function" "aggregator" {
  function_name = "${var.project_name}-aggregator"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 128

  filename         = "${path.module}/../lambdas/aggregator/package.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/aggregator/package.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.price_candles.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "aggregator_trigger" {
  event_source_arn  = aws_kinesis_stream.main.arn
  function_name     = aws_lambda_function.aggregator.arn
  starting_position = "LATEST"
  batch_size        = 50

  bisect_batch_on_function_error = true
  maximum_retry_attempts         = 3
}

# ── API Handler Lambda ─────────────────────────────
resource "aws_lambda_function" "api_handler" {
  function_name = "${var.project_name}-api-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  filename         = "${path.module}/../lambdas/api_handler/package.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambdas/api_handler/package.zip")

  environment {
    variables = {
      PRICES_TABLE   = aws_dynamodb_table.live_prices.name
      CANDLES_TABLE  = aws_dynamodb_table.price_candles.name
      ANOMALY_TABLE  = aws_dynamodb_table.anomalies.name
      DATA_LAKE_BUCKET = aws_s3_bucket.data_lake.id
      ATHENA_DATABASE  = aws_athena_database.main.name
      ATHENA_WORKGROUP = aws_athena_workgroup.main.name
      ATHENA_OUTPUT    = "s3://${aws_s3_bucket.data_lake.id}/athena-results/"
    }
  }
}
