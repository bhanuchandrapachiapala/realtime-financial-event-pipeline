"""
Aggregator Lambda — consumes Kinesis price records and builds OHLCV candles per symbol
per minute. Writes candles to DynamoDB (symbol, candle_timestamp) with TTL 30 days.
"""
import base64
import json
import os
from datetime import datetime, timezone, timedelta

import boto3
from botocore.exceptions import ClientError

TTL_DAYS = 30


def parse_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default


def round_timestamp_to_minute(ts: str) -> str:
    """Return ISO timestamp rounded down to the minute (e.g. ...T14:32:00Z)."""
    if not ts or not ts.strip():
        return datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        # Support both "Z" and "+00:00" and optional microseconds
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        rounded = dt.replace(second=0, microsecond=0)
        return rounded.isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError):
        return datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def lambda_handler(event, context):
    table_name = os.environ.get("DYNAMODB_TABLE")
    if not table_name:
        raise ValueError("DYNAMODB_TABLE must be set")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    ttl_seconds = int((datetime.now(timezone.utc) + timedelta(days=TTL_DAYS)).timestamp())
    processed = 0
    failed = 0

    for record in event.get("Records", []):
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            data = json.loads(payload)
        except (KeyError, ValueError, TypeError) as e:
            print(f"Bad record: {e}")
            failed += 1
            continue

        symbol = (data.get("symbol") or "").strip()
        ts = data.get("timestamp") or ""
        price = parse_float(data.get("price"))
        volume = int(data.get("volume", 0)) if data.get("volume") is not None else 0
        if not symbol:
            failed += 1
            continue

        candle_ts = round_timestamp_to_minute(ts)
        key = {"symbol": symbol, "candle_timestamp": candle_ts}

        try:
            # 1) Upsert: set close, volume, num_trades; init open/high/low if new candle
            table.update_item(
                Key=key,
                UpdateExpression="SET #close = :price, #vol = if_not_exists(#vol, :zero) + :v, #nt = if_not_exists(#nt, :zero) + :one, #open = if_not_exists(#open, :price), #high = if_not_exists(#high, :price), #low = if_not_exists(#low, :price), #ttl = :ttl",
                ExpressionAttributeNames={
                    "#close": "close",
                    "#vol": "volume",
                    "#nt": "num_trades",
                    "#open": "open",
                    "#high": "high",
                    "#low": "low",
                    "#ttl": "ttl",
                },
                ExpressionAttributeValues={
                    ":price": price,
                    ":v": volume,
                    ":one": 1,
                    ":zero": 0,
                    ":ttl": ttl_seconds,
                },
            )
            # 2) Raise high if this price is greater
            table.update_item(
                Key=key,
                UpdateExpression="SET #high = :price",
                ConditionExpression="attribute_not_exists(#high) OR #high < :price",
                ExpressionAttributeNames={"#high": "high"},
                ExpressionAttributeValues={":price": price},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise

        try:
            # 3) Lower low if this price is less
            table.update_item(
                Key=key,
                UpdateExpression="SET #low = :price",
                ConditionExpression="attribute_not_exists(#low) OR #low > :price",
                ExpressionAttributeNames={"#low": "low"},
                ExpressionAttributeValues={":price": price},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise

        processed += 1

    return {"processed": processed, "failed": failed}
