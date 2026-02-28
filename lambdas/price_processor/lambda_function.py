"""
Price Processor Lambda — consumes Kinesis records and writes to DynamoDB.
Triggered by Kinesis Data Stream. Records are base64-encoded JSON.
"""
import base64
import json
import os
from datetime import datetime, timezone, timedelta

import boto3

TTL_DAYS = 7


def build_item(record: dict) -> dict:
    """Build DynamoDB item: symbol (hash), timestamp (range), price as string, TTL."""
    symbol = record.get("symbol", "")
    ts = record.get("timestamp", "")
    if not symbol or not ts:
        return None

    # TTL: Unix timestamp in seconds, 7 days from now
    ttl_seconds = int((datetime.now(timezone.utc) + timedelta(days=TTL_DAYS)).timestamp())

    price = record.get("price")
    price_str = str(price) if price is not None else "0"

    item = {
        "symbol": symbol,
        "timestamp": ts,
        "price": price_str,
        "ttl": ttl_seconds,
    }
    if "volume" in record:
        item["volume"] = int(record["volume"]) if record["volume"] is not None else 0
    if "change_percent" in record:
        item["change_percent"] = str(record["change_percent"])
    if "source" in record:
        item["source"] = str(record["source"])

    return item


def lambda_handler(event, context):
    table_name = os.environ.get("DYNAMODB_TABLE")
    if not table_name:
        raise ValueError("DYNAMODB_TABLE must be set")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    written = 0
    failed = 0

    for record in event.get("Records", []):
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            data = json.loads(payload)
        except (KeyError, ValueError, TypeError) as e:
            print(f"Bad record: {e}")
            failed += 1
            continue

        item = build_item(data)
        if item is None:
            failed += 1
            continue

        try:
            table.put_item(Item=item)
            written += 1
        except Exception as e:
            print(f"PutItem failed for {item.get('symbol')}: {e}")
            failed += 1

    return {"batchItemFailures": [], "written": written, "failed": failed}
