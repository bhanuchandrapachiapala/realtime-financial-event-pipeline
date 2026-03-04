# Real-Time Financial Event Processing Engine

I wanted to build something that processes live market data the way real trading systems do — streaming, event-driven, not just CRUD with a database. FinPulse is exactly that: a pipeline that pulls stock prices for 10 companies every minute, streams them through AWS Kinesis, writes to DynamoDB and S3, detects price anomalies using Z-scores, sends email alerts, and serves everything to a live React dashboard.

**Live Dashboard:** [finpulse.vercel.app](https://realtime-financial-event-pipeline.vercel.app)

## How it works

Every 60 seconds, EventBridge wakes up a Lambda function that grabs the latest prices from Finnhub for AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA, NFLX, JPM, and V. Those prices get pushed into a Kinesis stream, where four consumers pick them up in parallel:

1. **Price Processor** writes each record to DynamoDB with a 7-day TTL so old data cleans itself up
2. **Anomaly Detector** calculates Z-scores against the last 30 data points — if a stock moves more than 2.5 standard deviations from its mean, it writes to the anomalies table and fires an email through SNS. Severity is HIGH if Z > 3.5, MEDIUM otherwise
3. **Aggregator** builds OHLCV candles (open, high, low, close, volume) per minute using conditional DynamoDB updates
4. **Firehose** archives every single event to S3, partitioned by year/month/day — the cold storage layer you can query with Athena using plain SQL

The React dashboard talks to API Gateway, which invokes a Lambda that reads from the three DynamoDB tables. Auto-refreshes every 60 seconds to match the ingestion cycle. Dark theme, Bloomberg-terminal vibes.

## What makes this interesting

**The fan-out pattern** — One Kinesis stream, four independent consumers reading the same data for completely different purposes. If the anomaly detector fails, prices still get stored. If Firehose lags, the dashboard still works. Nothing is tightly coupled.

**Anomaly detection** — Not just threshold-based ("alert if price > $X"). The Z-score approach adapts to each stock's own volatility. A $5 move on a $400 stock is normal, but the same move on a $20 stock is a red flag. The math handles this automatically.

**Hot and cold storage** — DynamoDB for the last 7 days (fast reads, dashboard queries), S3 for everything ever (cheap, queryable with Athena). Two storage tiers for two different access patterns.

**Infrastructure as code** — 13 Terraform files provision 42 AWS resources. One command to create everything, one command to destroy. No clicking around the console.

## Tech stack

| What | Why |
|------|-----|
| **Kinesis Data Streams** | Real-time streaming with parallel consumers. SQS would not work here — need multiple readers on the same data |
| **Lambda (x5)** | Ingester, price processor, anomaly detector, aggregator, API handler. Serverless, scales to zero when idle |
| **DynamoDB** | Fast reads for time-series data. On-demand billing, TTL for automatic cleanup, no connection pooling issues with Lambda |
| **S3 + Firehose** | Firehose buffers and writes to S3 automatically. Lifecycle moves data to IA at 30 days, Glacier at 90 |
| **EventBridge** | Cron-like scheduler for the 60-second ingestion cycle |
| **SNS** | Email alerts when anomalies are detected |
| **API Gateway** | HTTP API serving 5 REST endpoints to the dashboard |
| **Athena** | Serverless SQL over the S3 data lake. Pay per query |
| **CloudWatch** | Observability dashboard — Lambda invocations, errors, Kinesis throughput, DynamoDB writes |
| **Terraform** | All 42 resources defined in code. Version controlled, repeatable, reviewable |
| **GitHub Actions** | CI/CD — every push packages Lambdas and runs terraform apply |
| **React + Vite + Tailwind** | Frontend dashboard deployed on Vercel |
| **Finnhub API** | Free real-time stock data for 10 symbols |

## API endpoints

| Method | Path | What it returns |
|--------|------|----------------|
| GET | `/prices` | Latest price for all 10 symbols |
| GET | `/prices/{symbol}` | Price history (query params: hours, limit) |
| GET | `/anomalies` | Recent anomalies across all symbols |
| GET | `/candles/{symbol}` | OHLCV candles (query params: hours, limit) |
| GET | `/stats` | Pipeline health — events/hour, anomalies 24h, symbols tracked, status |

## Getting started

Make sure you have AWS CLI configured and Terraform 1.5+ installed. Get a free API key from [Finnhub](https://finnhub.io).

```bash
# Package Lambda functions
bash scripts/package_lambdas.sh

# Deploy everything to AWS
cd terraform
terraform init
terraform plan -var="alpha_vantage_api_key=YOUR_FINNHUB_KEY" -var="alert_email=you@example.com"
terraform apply    # same vars, type yes

# Check your email and confirm the SNS subscription

# Run the frontend
cd ../frontend
# Set .env: VITE_API_URL=<api_endpoint from terraform output>
npm install && npm run dev
```

To stop all charges:
```bash
cd terraform
terraform destroy -var="alpha_vantage_api_key=YOUR_KEY" -var="alert_email=YOUR_EMAIL"
```

Takes about 3 minutes to spin up, 2 minutes to tear down. I typically deploy before a demo and destroy after.

## Cost

The whole thing runs on about $30-40/month on AWS. Kinesis is the biggest cost at around $11/month for one shard. Lambda, DynamoDB, and S3 fall under free tier at this volume. Firehose and API Gateway add a few dollars. I keep it destroyed when not demoing and redeploy in 3 minutes when needed.

## What I would add next

WebSocket push instead of polling so the dashboard updates instantly. ML-based anomaly detection (isolation forest or LSTM) instead of just Z-scores. A mobile app for real-time alerts. And actually wiring the Athena query panel to run live SQL against the S3 data lake.

---

Built by **Bhanu Chandra Pachipala**
