# Punto 7 – Programmatic PySpark Analytical Pipeline (US 4.2)

Google Colab PySpark pipeline ([`punto7_analytics_colab.ipynb`](https://colab.research.google.com/drive/1CBB_D0g9144pPL8zfwOVABmRLJKc6h9u)) reading `s3://stock-big-data-bucket/trusted/stocks_enriched/` Parquet via the DataFrame API (`groupBy`, `Window`, `avg`, `max`, `rank`) and exporting refined Parquet datasets to `s3://stock-big-data-bucket/refined/analytics_results/`.

## Business Questions & Independent Query Cells

Each query cell in `punto7_analytics_colab.ipynb` runs independently after the setup cell (`base_df` + `with_daily_returns`):

| Notebook Cell | Business Questions Answered | Output S3 Prefix (`refined/analytics_results/`) |
|---|---|---|
| **Query 1** | **Q4 & Q5:** What are each stock's daily return %, 50-day Simple Moving Average (`SMA-50`), and % distance from `SMA-50` over time? | `daily_returns_sma50/` |
| **Query 2** | **Q2, Q3 & Q4:** How do GICS sectors compare by average/total trading volume, deduplicated market-cap rank, average daily return %, and daily volatility? | `sector_summary/` |
| **Query 3** | **Q1:** Which S&P 500 tickers delivered the highest total return % over the period (overall rank and rank within their sector)? | `top_gainers/` |
| **Query 4** | **Q2:** Which stocks are the top trading-volume leaders within each sector? | `volume_leaders_by_sector/` |

## How to Reproduce (Google Colab)

1. Open [`punto7_analytics_colab.ipynb`](https://colab.research.google.com/drive/1CBB_D0g9144pPL8zfwOVABmRLJKc6h9u) in Google Colab.
2. Run **Cell 1** (`!pip install -q pyspark boto3`).
3. Run **Cell 2** and enter your active AWS Academy temporary credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` from **AWS Details → Show**) to download `trusted/stocks_enriched/`.
4. Run **Cell 3** to initialize Spark (`local[*]`) and cache `base_df`.
5. Run any combination of **Query 1–4** cells in any order.
6. Run the final **Upload** cell to push the generated `.parquet` and `_SUCCESS` files (skipping `.crc`) to `s3://stock-big-data-bucket/refined/analytics_results/`.
