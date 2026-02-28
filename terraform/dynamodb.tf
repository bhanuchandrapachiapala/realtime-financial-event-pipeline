resource "aws_dynamodb_table" "live_prices" {
  name         = "${var.project_name}-live-prices"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"
  range_key    = "timestamp"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${var.project_name}-live-prices"
  }
}

resource "aws_dynamodb_table" "price_candles" {
  name         = "${var.project_name}-candles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"
  range_key    = "candle_timestamp"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "candle_timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${var.project_name}-candles"
  }
}

resource "aws_dynamodb_table" "anomalies" {
  name         = "${var.project_name}-anomalies"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"
  range_key    = "detected_at"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "detected_at"
    type = "S"
  }

  tags = {
    Name = "${var.project_name}-anomalies"
  }
}
