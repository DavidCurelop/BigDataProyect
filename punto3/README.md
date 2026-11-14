# Punto 3 – Automated Multi-Source Ingestion to S3 Raw Zone (US 2.3)

Single-command ingestion script (`s3_ingestion.py`) that lands all three raw data sources in S3:
1. **RDS MariaDB (`sp500.companies`, `sp500.fundamentals`)** -> `s3://<bucket>/raw/rds_companies/{table}/{table}.csv` (`pymysql` + `boto3 PutObject`)
2. **EC2 historical OHLCV (`/data/ohlcv/*.csv`)** -> `s3://<bucket>/raw/ec2_historical_ohlcv/` (`aws s3 sync`)
3. **Yahoo Finance daily bars** -> `s3://<bucket>/raw/yfinance_quotes/dt=YYYY-MM-DD/quotes.json` (NDJSON via `boto3 PutObject`)

## EC2 Environment (Amazon Linux 2023)
- **IAM Role:** `LabRole` instance profile attached (no hardcoded AWS keys needed).
- **System tools:** `/usr/bin/aws`, `/usr/bin/python3`, `/usr/bin/flock`, and `crond` (`cronie`).
- **Staged data:** `/data/ohlcv/` (503 ticker CSVs).

## Setup on EC2 (`/home/ec2-user`)
1. Ensure `cronie` is installed and running:
   ```bash
   sudo dnf install -y cronie
   sudo systemctl enable --now crond
   ```
2. Ensure `/home/ec2-user/.env` includes `S3_BUCKET` (plus `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and optional `AWS_REGION`).
3. Install Python dependencies into `.venv`:
   ```bash
   cd /home/ec2-user
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

## Manual & Cron-Simulated Test
Test from a stripped environment (mirrors `cron`) before scheduling:
```bash
env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/sh -c 'cd /home/ec2-user && .venv/bin/python s3_ingestion.py'
```

## EC2 Crontab Setup
Edit crontab (`crontab -e`) to run weekdays at 23:00 UTC (after US market close) with `flock` preventing overlapping runs:
```cron
0 23 * * 1-5 cd /home/ec2-user && /usr/bin/flock -n /tmp/s3_ingestion.lock .venv/bin/python s3_ingestion.py >> cron_ingest.log 2>&1
```

## Verification
```bash
crontab -l
tail -n 30 /home/ec2-user/cron_ingest.log
aws s3 ls s3://$S3_BUCKET/raw/ --recursive --human-readable --summarize
```
