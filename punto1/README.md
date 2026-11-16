# Punto 1 – Case Study, Analytical Questions & AWS Architecture (US 1.1 & US 1.2)

End-to-end **S&P 500 Equities Lakehouse** on AWS (`us-east-1`) combining company fundamentals, historical daily OHLCV CSVs, and automated Yahoo Finance daily quote updates across Medallion S3 zones (`raw/` -> `trusted/` -> `refined/`).

- **Architecture Diagram:** [Lucidchart — ST0263 Big Data AWS Architecture](https://lucid.app/lucidchart/cfae0167-5d6b-4944-b8d5-1c3cd50f1aa1/edit?page=EwUbr1p0YOTyF)

## Business Questions (Q1–Q5)
1. **Q1 — Top Tickers by Total Return %:** Which S&P 500 tickers delivered the highest cumulative return over the observed period?
2. **Q2 — Average Trading Volume & Volume Leaders by Sector:** Which sectors record the highest average/total daily trading volume, and which tickers lead each sector?
3. **Q3 — Sector Market-Cap Ranking:** How do sectors rank by total deduplicated market capitalization and average company market cap?
4. **Q4 — Daily Return % & Volatility by Sector:** What are daily stock percentage returns, and which sectors have the highest average daily return and volatility?
5. **Q5 — 50-Day Simple Moving Average (`SMA-50`):** How does each stock's latest closing price compare against its rolling 50-day SMA (`pct_vs_sma50`)?

## Dataset Schemas
- **RDS MariaDB (`sp500.companies`)**: `symbol` (PK), `security`, `gics_sector`, `gics_sub_industry`, `headquarters_location`, `date_added`, `cik`, `founded`.
- **RDS MariaDB (`sp500.fundamentals`)**: `symbol` (PK/FK), `name`, `sector`, `price`, `price_earnings`, `dividend_yield`, `earnings_share`, `week_52_low`, `week_52_high`, `market_cap`, `ebitda`, `price_sales`, `price_book`, `sec_filings`.
- **EC2 Historical OHLCV (`/data/ohlcv/*.csv`)**: `date`, `ticker`, `open`, `high`, `low`, `close`, `volume`.
- **Yahoo Finance Daily Bars (`raw/yfinance_quotes/dt=YYYY-MM-DD/quotes.json`)**: NDJSON with `date`, `ticker`, `open`, `high`, `low`, `close`, `volume`.

## AWS Infrastructure & Security
- **S3 Bucket (`stock-big-data-bucket`):** `raw/` (RDS CSVs, EC2 historical CSVs, Yahoo Finance NDJSON), `trusted/stocks_enriched/` (Snappy Parquet partitioned by `sector`), `refined/analytics_results/` (PySpark Parquet tables), and `athena-results/`.
- **IAM & Network Security:** AWS Academy `LabRole` / `LabInstanceProfile` (zero hardcoded credentials on EC2, Glue, and EMR), RDS MariaDB (`:3306`) restricted to VPC/SG, and `sp500-ec2-sg` exposing TCP `22`, `8000`, and `8501`.
