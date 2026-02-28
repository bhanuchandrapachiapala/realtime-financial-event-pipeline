"""
API Handler Lambda — HTTP API routes for prices, anomalies, candles, and pipeline stats.
Uses DynamoDB (PRICES_TABLE, CANDLES_TABLE, ANOMALY_TABLE). Returns JSON with CORS headers.
"""
import json
import os
from datetime import datetime, timezone, timedelta

import boto3

SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
}


def response(body, status_code=200):
    return {"statusCode": status_code, "headers": CORS_HEADERS, "body": json.dumps(body)}


def error_response(message: str, status_code=400):
    return response({"error": message}, status_code)


def get_table(name_env: str):
    table_name = os.environ.get(name_env)
    if not table_name:
        raise ValueError(f"{name_env} must be set")
    return boto3.resource("dynamodb").Table(table_name)


def get_latest_prices_all(prices_table) -> dict:
    """GET /prices — latest price for all 5 symbols."""
    results = {}
    for symbol in SYMBOLS:
        r = prices_table.query(
            KeyConditionExpression="symbol = :s",
            ExpressionAttributeValues={":s": symbol},
            Limit=1,
            ScanIndexForward=False,
        )
        items = r.get("Items", [])
        if items:
            item = items[0]
            results[symbol] = {
                "symbol": item.get("symbol"),
                "price": item.get("price"),
                "timestamp": item.get("timestamp"),
                "volume": item.get("volume"),
                "change_percent": item.get("change_percent"),
            }
    return response({"prices": results})


def get_price_history(prices_table, symbol: str, query_params: dict) -> dict:
    """GET /prices/{symbol} — history with optional hours (default 24) and limit (default 100)."""
    symbol = (symbol or "").upper().strip()
    if symbol not in SYMBOLS:
        return error_response(f"Unknown symbol: {symbol}", 400)
    hours = int(query_params.get("hours", 24)) if query_params else 24
    limit = int(query_params.get("limit", 100)) if query_params else 100
    hours = max(1, min(hours, 168))
    limit = max(1, min(limit, 500))
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat().replace("+00:00", "Z")
    r = prices_table.query(
        KeyConditionExpression="symbol = :s AND #ts >= :since",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={":s": symbol, ":since": since},
        Limit=limit,
        ScanIndexForward=False,
    )
    items = r.get("Items", [])
    return response({"symbol": symbol, "prices": items, "count": len(items)})


def get_anomalies(anomaly_table, query_params: dict) -> dict:
    """GET /anomalies — recent anomalies across all symbols."""
    limit = int(query_params.get("limit", 50)) if query_params else 50
    limit = max(1, min(limit, 200))
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    # Scan with filter (no GSI); for larger scale you’d use a GSI on detected_at
    r = anomaly_table.scan(
        FilterExpression="detected_at >= :since",
        ExpressionAttributeValues={":since": since},
        Limit=limit * 2,
    )
    items = r.get("Items", [])
    while r.get("LastEvaluatedKey") and len(items) < limit:
        r = anomaly_table.scan(
            FilterExpression="detected_at >= :since",
            ExpressionAttributeValues={":since": since},
            ExclusiveStartKey=r["LastEvaluatedKey"],
            Limit=limit * 2,
        )
        items.extend(r.get("Items", []))
    items = sorted(items, key=lambda x: x.get("detected_at", ""), reverse=True)[:limit]
    return response({"anomalies": items, "count": len(items)})


def get_candles(candles_table, symbol: str, query_params: dict) -> dict:
    """GET /candles/{symbol} — OHLCV candles with optional hours and limit."""
    symbol = (symbol or "").upper().strip()
    if symbol not in SYMBOLS:
        return error_response(f"Unknown symbol: {symbol}", 400)
    hours = int(query_params.get("hours", 24)) if query_params else 24
    limit = int(query_params.get("limit", 100)) if query_params else 100
    hours = max(1, min(hours, 168))
    limit = max(1, min(limit, 500))
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat().replace("+00:00", "Z")
    r = candles_table.query(
        KeyConditionExpression="symbol = :s AND candle_timestamp >= :since",
        ExpressionAttributeValues={":s": symbol, ":since": since},
        Limit=limit,
        ScanIndexForward=False,
    )
    items = r.get("Items", [])
    return response({"symbol": symbol, "candles": items, "count": len(items)})


def get_stats(prices_table, anomaly_table) -> dict:
    """GET /stats — events last hour, anomalies 24h, symbols tracked, latest prices, pipeline status."""
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    events_last_hour = 0
    latest_prices = {}
    for symbol in SYMBOLS:
        r = prices_table.query(
            KeyConditionExpression="symbol = :s AND #ts >= :t",
            ExpressionAttributeNames={"#ts": "timestamp"},
            ExpressionAttributeValues={":s": symbol, ":t": one_hour_ago},
            Select="COUNT",
        )
        events_last_hour += r.get("Count", 0)
        # latest price for stats
        r2 = prices_table.query(
            KeyConditionExpression="symbol = :s",
            ExpressionAttributeValues={":s": symbol},
            Limit=1,
            ScanIndexForward=False,
        )
        for item in r2.get("Items", []):
            latest_prices[symbol] = item.get("price")
    anomalies_24h = 0
    r = anomaly_table.scan(
        FilterExpression="detected_at >= :t",
        ExpressionAttributeValues={":t": day_ago},
        Select="COUNT",
    )
    anomalies_24h = r.get("Count", 0)
    while r.get("LastEvaluatedKey"):
        r = anomaly_table.scan(
            FilterExpression="detected_at >= :t",
            ExpressionAttributeValues={":t": day_ago},
            ExclusiveStartKey=r["LastEvaluatedKey"],
            Select="COUNT",
        )
        anomalies_24h += r.get("Count", 0)
    return response({
        "events_last_hour": events_last_hour,
        "anomalies_24h": anomalies_24h,
        "symbols_tracked": SYMBOLS,
        "latest_prices": latest_prices,
        "pipeline_status": "operational",
    })


def lambda_handler(event, context):
    method = (event.get("requestContext") or {}).get("http", {}).get("method", "GET")
    raw_path = event.get("rawPath", "") or event.get("path", "")
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    try:
        prices_table = get_table("PRICES_TABLE")
        candles_table = get_table("CANDLES_TABLE")
        anomaly_table = get_table("ANOMALY_TABLE")
    except ValueError as e:
        return error_response(str(e), 500)

    if method != "GET":
        return error_response("Method not allowed", 405)

    if raw_path == "/prices" and not path_params:
        return get_latest_prices_all(prices_table)
    if raw_path.startswith("/prices/"):
        symbol = path_params.get("symbol", raw_path.split("/prices/")[-1].split("?")[0])
        return get_price_history(prices_table, symbol, query_params)
    if raw_path == "/anomalies":
        return get_anomalies(anomaly_table, query_params)
    if raw_path.startswith("/candles/"):
        symbol = path_params.get("symbol", raw_path.split("/candles/")[-1].split("?")[0])
        return get_candles(candles_table, symbol, query_params)
    if raw_path == "/stats":
        return get_stats(prices_table, anomaly_table)

    return error_response("Not found", 404)
