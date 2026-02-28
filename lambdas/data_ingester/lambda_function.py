"""
Data Ingester Lambda — fetches live quotes from Alpha Vantage and pushes to Kinesis.
Triggered by EventBridge every 60 seconds.
"""
import json
import os
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

import boto3

SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
GLOBAL_QUOTE_URL = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={apikey}"


def fetch_quote(symbol: str, api_key: str) -> dict | None:
    """Fetch GLOBAL_QUOTE for one symbol. Returns parsed record or None on failure."""
    url = GLOBAL_QUOTE_URL.format(symbol=symbol, apikey=api_key)
    req = Request(url, headers={"User-Agent": "FinPulse-Ingester/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        print(f"Failed to fetch {symbol}: {e}")
        return None

    quote = data.get("Global Quote")
    if not quote or not isinstance(quote, dict):
        return None

    # Alpha Vantage GLOBAL_QUOTE uses keys like "05. price", "06. volume", "10. change percent"
    price = quote.get("05. price", "").strip()
    volume = quote.get("06. volume", "").strip()
    change_pct = quote.get("10. change percent", "").strip().removesuffix("%")

    if not price:
        return None

    try:
        price_f = float(price)
        volume_f = int(volume) if volume else 0
        change_f = float(change_pct) if change_pct else 0.0
    except (ValueError, TypeError):
        return None

    return {
        "symbol": symbol,
        "price": price_f,
        "volume": volume_f,
        "change_percent": change_f,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "alpha_vantage",
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
