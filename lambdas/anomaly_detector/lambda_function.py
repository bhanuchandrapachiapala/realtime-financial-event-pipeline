"""
Anomaly Detector Lambda — consumes Kinesis price records, computes Z-score vs last 30
prices in DynamoDB, and writes anomalies + SNS alerts when threshold is exceeded.
"""
import base64
import json
import os
import statistics
from datetime import datetime, timezone

import boto3

DEFAULT_Z_THRESHOLD = 2.5
HISTORY_LIMIT = 30
HIGH_SEVERITY_Z = 3.5


def parse_price(value) -> float:
    """Parse price from JSON (float) or DynamoDB string."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return 0.0


def get_last_prices(dynamodb, table_name: str, symbol: str, limit: int = HISTORY_LIMIT) -> list[float]:
    """Query last N prices for symbol from live_prices (range key timestamp, desc)."""
    table = dynamodb.Table(table_name)
    resp = table.query(
        KeyConditionExpression="symbol = :sym",
        ExpressionAttributeValues={":sym": symbol},
        Limit=limit,
        ScanIndexForward=False,
        ProjectionExpression="price",
    )
    prices = []
    for item in resp.get("Items", []):
        p = parse_price(item.get("price"))
        prices.append(p)
    return prices


def lambda_handler(event, context):
    table_name = os.environ.get("DYNAMODB_TABLE")
    anomaly_table_name = os.environ.get("ANOMALY_TABLE")
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
    try:
        z_threshold = float(os.environ.get("Z_SCORE_THRESHOLD", DEFAULT_Z_THRESHOLD))
    except (TypeError, ValueError):
        z_threshold = DEFAULT_Z_THRESHOLD

    if not table_name or not anomaly_table_name or not sns_topic_arn:
        raise ValueError("DYNAMODB_TABLE, ANOMALY_TABLE, and SNS_TOPIC_ARN must be set")

    dynamodb = boto3.resource("dynamodb")
    sns = boto3.client("sns")
    anomaly_table = dynamodb.Table(anomaly_table_name)
    detected = 0
    failed = 0

    for record in event.get("Records", []):
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            data = json.loads(payload)
        except (KeyError, ValueError, TypeError) as e:
            print(f"Bad record: {e}")
            failed += 1
            continue

        symbol = data.get("symbol", "").strip()
        ts = data.get("timestamp", "")
        current_price = parse_price(data.get("price"))
        if not symbol or not ts:
            failed += 1
            continue

        history = get_last_prices(dynamodb, table_name, symbol)
        if len(history) < 2:
            continue

        mean_price = statistics.mean(history)
        try:
            stdev = statistics.stdev(history)
        except statistics.StatisticsError:
            stdev = 0.0
        if stdev <= 0:
            continue

        z_score = (current_price - mean_price) / stdev
        if abs(z_score) <= z_threshold:
            continue

        direction = "SPIKE" if current_price > mean_price else "DROP"
        deviation_pct = ((current_price - mean_price) / mean_price * 100) if mean_price else 0.0
        severity = "HIGH" if abs(z_score) > HIGH_SEVERITY_Z else "MEDIUM"
        detected_at = ts or datetime.now(timezone.utc).isoformat()

        anomaly_item = {
            "symbol": symbol,
            "detected_at": detected_at,
            "direction": direction,
            "current_price": str(current_price),
            "mean_price": str(mean_price),
            "deviation_percent": str(round(deviation_pct, 4)),
            "z_score": str(round(z_score, 4)),
            "severity": severity,
        }
        try:
            anomaly_table.put_item(Item=anomaly_item)
        except Exception as e:
            print(f"Failed to write anomaly for {symbol}: {e}")
            failed += 1
            continue

        alert_body = {
            "symbol": symbol,
            "direction": direction,
            "current_price": current_price,
            "mean_price": mean_price,
            "deviation_percent": round(deviation_pct, 4),
            "z_score": round(z_score, 4),
            "severity": severity,
            "detected_at": detected_at,
        }
        try:
            sns.publish(
                TopicArn=sns_topic_arn,
                Subject=f"FinPulse Anomaly: {symbol} {direction} ({severity})",
                Message=json.dumps(alert_body, indent=2),
            )
        except Exception as e:
            print(f"SNS publish failed for {symbol}: {e}")

        detected += 1

    return {"anomalies_detected": detected, "failed": failed}
