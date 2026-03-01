"""
Data Ingester Lambda — fetches live quotes from Finnhub and pushes to Kinesis.
Triggered by EventBridge every 60 seconds.
"""
import json
import os
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

import boto3

SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "JPM", "V"]
FINNHUB_QUOTE_URL = "https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"


def fetch_quote(symbol: str, api_key: str) -> dict | None:
    """Fetch quote for one symbol from Finnhub. Returns parsed record or None on failure."""
    url = FINNHUB_QUOTE_URL.format(symbol=symbol, api_key=api_key)
    req = Request(url, headers={"User-Agent": "FinPulse-Ingester/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        print(f"Failed to fetch {symbol}: {e}")
        return None

    if not isinstance(data, dict):
        return None

    # Finnhub quote: c (current price), v (volume), dp (percent change)
    price_raw = data.get("c")
    volume_raw = data.get("v")
    change_pct_raw = data.get("dp")

    if price_raw is None:
        return None

    try:
        price_f = float(price_raw)
        volume_f = int(volume_raw) if volume_raw is not None else 0
        change_f = float(change_pct_raw) if change_pct_raw is not None else 0.0
    except (ValueError, TypeError):
        return None

    return {
        "symbol": symbol,
        "price": price_f,
        "volume": volume_f,
        "change_percent": change_f,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "finnhub",
    }


def lambda_handler(event, context):
    stream_name = os.environ.get("KINESIS_STREAM_NAME")
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not stream_name or not api_key:
        raise ValueError("KINESIS_STREAM_NAME and ALPHA_VANTAGE_API_KEY must be set")

    kinesis = boto3.client("kinesis")
    put_count = 0

    for symbol in SYMBOLS:
        record = fetch_quote(symbol, api_key)
        if record is None:
            continue
        payload = json.dumps(record)
        kinesis.put_record(
            StreamName=stream_name,
            Data=payload.encode("utf-8"),
            PartitionKey=symbol,
        )
        put_count += 1

    return {"statusCode": 200, "records_put": put_count, "symbols": SYMBOLS}
