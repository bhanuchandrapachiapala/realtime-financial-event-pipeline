resource "aws_athena_workgroup" "main" {
  name = "${var.project_name}-workgroup"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake.id}/athena-results/"
    }

    enforce_workgroup_configuration = true
  }
}

resource "aws_athena_database" "main" {
  name   = "${var.project_name}_db"
  bucket = aws_s3_bucket.data_lake.id
}

# Note: The Athena table for raw data will be created via a SQL query
# after Firehose starts delivering data. Add this as a named query:
resource "aws_athena_named_query" "create_table" {
  name      = "create-raw-prices-table"
  workgroup = aws_athena_workgroup.main.name
  database  = aws_athena_database.main.name
  query     = <<-EOF
    CREATE EXTERNAL TABLE IF NOT EXISTS raw_prices (
      symbol STRING,
      price DOUBLE,
      volume BIGINT,
      timestamp STRING,
      source STRING
    )
    PARTITIONED BY (year STRING, month STRING, day STRING)
    ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
    LOCATION 's3://${aws_s3_bucket.data_lake.id}/raw-data/'
    TBLPROPERTIES ('has_encrypted_data'='false');
  EOF
}
