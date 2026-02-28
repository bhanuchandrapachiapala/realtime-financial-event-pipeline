# ⚡ FinPulse — Real-Time Financial Event Processing Engine

I wanted to build something that processes live market data the way real trading systems do — streaming, event-driven, not just CRUD with a database. FinPulse is exactly that: a pipeline that pulls stock prices for AAPL, GOOGL, MSFT, AMZN, and TSLA every minute, streams them through AWS Kinesis, writes to DynamoDB and S3, detects price anomalies with Z-scores, and serves everything to a React dashboard. No polling a REST API every few seconds; events flow once and get consumed by multiple processors in parallel.

## Architecture

Here's how data flows through the system — from the moment a stock price is fetched to when it shows up on the dashboard or triggers an anomaly alert.

```
                    ┌─────────────────┐
                    │  EventBridge    │
                    │  (every 1 min) │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐     ┌──────────────┐
                    │  data_ingester  │────▶│   Kinesis    │
                    │  Lambda         │     │   Stream     │
                    └─────────────────┘     └──────┬──────┘
                                                    │
              ┌─────────────────┬───────────────────┼───────────────────┐
              ▼                 ▼                   ▼                   ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ price_       │  │ anomaly_     │  │ aggregator   │  │  Firehose    │
     │ processor    │  │ detector     │  │ Lambda       │  │              │
     └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
            │                 │                 │                 │
            ▼                 ▼                 ▼                 ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ live_prices  │  │ anomalies    │  │ price_candles│  │  S3 data lake│
     │ (DynamoDB)   │  │ (DynamoDB)   │  │ (DynamoDB)   │  │  (+ Athena)  │
     └──────┬───────┘  └──────┬───────┘  └──────────────┘  └──────────────┘
            │                 │
            │                 ▼
            │          ┌──────────────┐
            │          │  SNS email   │
            │          │  alerts      │
            │          └──────────────┘
            │
            └────────────────┬─────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ API Gateway +    │
                    │ api_handler      │
                    │ Lambda          │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ React dashboard  │
                    └─────────────────┘
```

## How it works

Every 60 seconds, EventBridge wakes up a Lambda function that grabs the latest prices from Alpha Vantage. Those prices get pushed into a Kinesis stream, where three separate Lambda consumers pick them up in parallel: one writes each record to the live_prices DynamoDB table, another builds OHLCV minute candles and writes to price_candles, and the third runs a Z-score check against the last 30 prices — if it crosses the threshold, it writes to the anomalies table and sends an email via SNS. At the same time, Firehose is reading from the same stream and archiving every event to S3 with date-partitioned paths. The React app talks to API Gateway, which invokes a single Lambda that reads from the three DynamoDB tables (and can eventually query S3 with Athena). So one event triggers multiple writers and one archive path; no duplicated API calls.

## The cool parts

- **Anomaly detection** — The system calculates Z-scores against the last 30 price points. If something moves more than 2.5 standard deviations, you get an email. Severity is HIGH if Z > 3.5, else MEDIUM. Direction is SPIKE or DROP.

- **Data lake** — Every single event gets archived to S3 through Firehose (prefix like `raw-data/year=.../month=.../day=...`). You can query years of data with plain SQL through Athena. The dashboard has a demo query panel; wiring Athena to it is optional.

- **Dashboard** — Auto-refreshes every 60 seconds, shows live prices, historical charts (1h / 6h / 24h), pipeline stats, and an anomaly alert feed. Dark theme, Bloomberg-terminal vibes.

## Tech stack

| AWS service      | What it does |
|------------------|--------------|
| EventBridge Scheduler | Fires the data ingester Lambda every 1 minute |
| Lambda           | data_ingester (Alpha Vantage → Kinesis), price_processor, anomaly_detector, aggregator, api_handler |
| Kinesis Data Streams | Buffers price events; multiple consumers read in parallel |
| Firehose         | Streams Kinesis data to S3 (data lake) |
| DynamoDB         | live_prices, price_candles, anomalies tables |
| S3               | Raw event archive (lifecycle: 30d → IA, 90d → Glacier) |
| SNS              | Email alerts when an anomaly is detected |
| API Gateway (HTTP API) | Routes GET /prices, /prices/{symbol}, /anomalies, /candles/{symbol}, /stats to api_handler |
| Athena (optional) | SQL over S3 data |

## Project structure

```
.
├── .github/workflows/
│   └── deploy.yml          # CI: pytest, package Lambdas, terraform plan/apply
├── frontend/                # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/      # StatsBar, PriceTicker, PriceChart, AnomalyFeed, QueryPanel
│   │   ├── services/
│   │   │   └── api.js       # Axios wrapper for API
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── lambdas/
│   ├── data_ingester/       # EventBridge → Alpha Vantage → Kinesis
│   ├── price_processor/    # Kinesis → live_prices
│   ├── anomaly_detector/   # Kinesis → Z-score → anomalies + SNS
│   ├── aggregator/         # Kinesis → OHLCV candles
│   └── api_handler/        # API Gateway → DynamoDB
├── scripts/
│   └── package_lambdas.sh  # Zip each Lambda for Terraform
└── terraform/               # All infra (main, variables, outputs, per-service .tf files)
```

## Getting started

First make sure you have AWS CLI configured and Terraform installed (1.5+). Grab a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key). Then:

1. **Package the Lambdas**  
   `bash scripts/package_lambdas.sh`

2. **Deploy infra**  
   From `terraform/`:  
   `terraform init`  
   `terraform plan -var="alpha_vantage_api_key=YOUR_KEY" -var="alert_email=you@example.com"`  
   `terraform apply` (same vars)

3. **Confirm SNS**  
   Check your email and confirm the SNS subscription so anomaly alerts are delivered.

4. **Run the frontend**  
   In `frontend/`, set `.env`: `VITE_API_URL=https://your-api-gateway-url` (from Terraform output). Then `npm install && npm run dev`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /prices | Latest price for all 5 symbols |
| GET | /prices/{symbol} | Price history (query: hours, limit) |
| GET | /anomalies | Recent anomalies (query: limit) |
| GET | /candles/{symbol} | OHLCV candles (query: hours, limit) |
| GET | /stats | Pipeline stats (events/hour, anomalies 24h, status) |

## Cost

This whole thing runs on about $30–40/month on AWS. Kinesis is the biggest cost at ~$11/month for one shard. Everything else falls under free tier or costs pennies (Lambda, DynamoDB on-demand, S3, SNS). Firehose and data transfer add a bit; Athena you pay per query if you use it.

## What I'd add next

If I had more time, I'd add WebSocket push instead of polling so the dashboard updates the second new data lands, real ML-based anomaly detection instead of just Z-scores, and maybe a mobile app. Oh, and actually wiring the Athena query panel to run real SQL against the S3 bucket.

---

Built by Bhanu Chandra Pachipala
