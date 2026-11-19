# Punto 2 – Multi-Source Data Setup (RDS MariaDB, EC2 Files & Internet URLs)

Sets up and verifies the three raw data sources required for the S&P 500 lakehouse:

1. **Relational Database (Amazon RDS MariaDB — `sp500`)**: `companies` and `fundamentals` tables loaded from public GitHub CSV datasets.
2. **EC2 Flat Files (`/data/ohlcv/*.csv`)**: Historical 1-year daily OHLCV CSV files staged on the EC2 Linux instance.
3. **Internet URLs**:
   - GitHub S&P 500 Constituents CSV: `https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv`
   - GitHub S&P 500 Financials CSV: `https://raw.githubusercontent.com/datasets/s-and-p-500-companies-financials/main/data/constituents-financials.csv`
   - Yahoo Finance v8 Chart JSON API: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d`

## Files
- [`schema.sql`](schema.sql) — DDL creating database `sp500` and tables `companies` and `fundamentals`.
- [`load_and_verify.py`](load_and_verify.py) — Downloads GitHub S&P 500 CSVs, loads `companies` and `fundamentals` into RDS MariaDB, and runs [`verify.sql`](verify.sql).
- [`verify.sql`](verify.sql) — SQL row-count and top-10 market-cap join checks.
- [`stage_and_verify_ohlcv.py`](stage_and_verify_ohlcv.py) — Fetches 1-year daily bars per ticker from Yahoo Finance and writes/validates `/data/ohlcv/{TICKER}.csv`.

## How to Reproduce

### 1. Populate & Verify RDS MariaDB (`sp500`)
Configure `.env` (from `.env.example`) with `DB_HOST`, `DB_PORT=3306`, `DB_USER`, and `DB_PASSWORD`, ensure VPC/Security Group allows port `3306`, and run:
```bash
python punto2/load_and_verify.py
```

### 2. Stage & Verify Historical OHLCV CSVs on EC2
SSH into the EC2 instance (`ec2-user`), ensure `/data/ohlcv` is writable, and run:
```bash
sudo mkdir -p /data/ohlcv && sudo chown ec2-user:ec2-user /data/ohlcv
python3 stage_and_verify_ohlcv.py
```
The script verifies `>= 450` CSV files, `>= 100,000` total rows, valid `YYYY-MM-DD` dates, and the 7-column schema (`date,ticker,open,high,low,close,volume`).
