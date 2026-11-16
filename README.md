# ST0263 Big Data Project 2 — S&P 500 Equities Lakehouse on AWS

Universidad EAFIT — **ST0263 Tópicos Especiales en Telemática (2026-1)** ([project spec](ST0263-261-proyecto2.pdf)).

End-to-end AWS Data Lakehouse (`us-east-1`, S3 bucket `stock-big-data-bucket`, Glue Data Catalog `stocks_db.stocks_enriched`) ingesting S&P 500 company fundamentals (RDS MariaDB), historical OHLCV CSVs (EC2), and daily Yahoo Finance JSON bars into Medallion S3 zones (`raw/` → `trusted/` → `refined/`).

- **Architecture Diagram:** [Lucidchart — ST0263 Big Data AWS Architecture](https://lucid.app/lucidchart/cfae0167-5d6b-4944-b8d5-1c3cd50f1aa1/edit?page=EwUbr1p0YOTyF)
- **Public API Gateway (`prod`):** `https://ldufp8c5w2.execute-api.us-east-1.amazonaws.com/prod`
- **Streamlit Dashboard:** `http://54.224.176.52:8501` (FastAPI Swagger: `http://54.224.176.52:8000/docs`)

## Business Questions (Q1–Q5)

1. **Q1 — Top Tickers by Total Return %:** Which S&P 500 tickers delivered the highest cumulative return over the observed period (overall and within each sector)?
2. **Q2 — Average Trading Volume & Volume Leaders by Sector:** Which sectors record the highest average/total daily trading volume, and which stocks lead trading volume within each sector?
3. **Q3 — Sector Market-Cap Ranking:** How do sectors rank by total deduplicated market capitalization and average company market cap?
4. **Q4 — Daily Return % & Volatility by Sector:** What are the daily percentage returns per stock, and which sectors exhibit the highest average daily return and daily volatility?
5. **Q5 — 50-Day Simple Moving Average (`SMA-50`):** How does each ticker's daily closing price compare against its rolling 50-day Simple Moving Average (`SMA-50` and `% vs SMA-50`)?

## Repository Structure

| Path | Scope | Key Files |
|---|---|---|
| [`punto1/`](punto1/) | **Punto 1:** Case study, schemas, Q1–Q5 & AWS/IAM architecture | [`README.md`](punto1/README.md) |
| [`punto2/`](punto2/) | **Punto 2:** RDS MariaDB (`sp500`) & EC2 historical OHLCV staging | `schema.sql`, `load_and_verify.py`, `stage_and_verify_ohlcv.py`, `verify.sql` |
| [`punto3/`](punto3/) | **Punto 3:** Automated multi-source S3 raw ingestion (`crond`) | [`s3_ingestion.py`](punto3/s3_ingestion.py), [`README.md`](punto3/README.md) |
| [`punto4/`](punto4/) | **Punto 4:** Raw-to-Trusted AWS Glue 4.0 PySpark ETL job | [`sp500_raw_to_trusted.py`](punto4/sp500_raw_to_trusted.py), [`README.md`](punto4/README.md) |
| [`EMRScripts/`](EMRScripts/) | **Punto 5:** EMR Hive & SparkSQL Glue Catalog verification | `verify_hive.q`, `verify_sparksql.py`, [`README.md`](EMRScripts/README.md) |
| [`SQLScripts/`](SQLScripts/) | **Punto 6:** Descriptive SQL (Q1–Q5) for Athena, EMR Hive/Hue & SparkSQL | `athena/q*.sql`, `emr/q*.sql`, [`README.md`](SQLScripts/README.md) |
| [`punto7/`](punto7/) | **Punto 7:** Programmatic PySpark pipeline ([Colab notebook](https://colab.research.google.com/drive/1CBB_D0g9144pPL8zfwOVABmRLJKc6h9u)) → `refined/analytics_results/` | [`punto7_analytics_colab.ipynb`](punto7/punto7_analytics_colab.ipynb), [`README.md`](punto7/README.md) |
| [`punto8/`](punto8/) | **Punto 8:** FastAPI (`:8000`), API Gateway (`prod`), Streamlit (`:8501`) & Matplotlib charts | [`api.py`](punto8/api.py), [`dashboard.py`](punto8/dashboard.py), [`athena_matplotlib_charts.ipynb`](punto8/athena_matplotlib_charts.ipynb), [`README.md`](punto8/README.md) |

## Quick Setup

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

See the sub-directory READMEs ([`punto1/README.md`](punto1/README.md), [`punto3/README.md`](punto3/README.md), [`punto4/README.md`](punto4/README.md), [`EMRScripts/README.md`](EMRScripts/README.md), [`SQLScripts/README.md`](SQLScripts/README.md), [`punto7/README.md`](punto7/README.md), [`punto8/README.md`](punto8/README.md)) for per-stage AWS and execution instructions.
