from __future__ import annotations

from functools import lru_cache
import io
import json
import os
from typing import Optional

import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

BUCKET = os.environ.get("S3_BUCKET", "stock-big-data-bucket")
REGION = os.environ.get("AWS_REGION", "us-east-1")
REFINED_PREFIX = "refined/analytics_results"
TABLES = ("daily_returns_sma50", "sector_summary", "top_gainers", "volume_leaders_by_sector")

app = FastAPI(title="S&P 500 Lakehouse Analytics API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


# shortcut: caches refined Parquet tables in process RAM; restart uvicorn after daily pipeline refresh
@lru_cache(maxsize=len(TABLES))
def load_table(table: str) -> pd.DataFrame:
    if table not in TABLES:
        raise ValueError(f"Unknown table: {table}")
    s3 = boto3.client("s3", region_name=REGION)
    prefix = f"{REFINED_PREFIX}/{table}/"
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    keys = [obj["Key"] for obj in resp.get("Contents", []) if obj["Key"].endswith(".parquet")]
    assert keys, f"No parquet files found at s3://{BUCKET}/{prefix}"

    frames = [pd.read_parquet(io.BytesIO(s3.get_object(Bucket=BUCKET, Key=k)["Body"].read())) for k in keys]
    df = pd.concat(frames, ignore_index=True)
    assert not df.empty, f"Loaded empty parquet table: {table}"

    for col in ("date", "start_date", "end_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
    return df


def to_records(df: pd.DataFrame) -> list[dict]:
    # to_json converts NaN/NaT/numpy scalars cleanly into JSON-safe values
    return json.loads(df.to_json(orient="records"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "bucket": BUCKET, "tables": {t: len(load_table(t)) for t in TABLES}}


@app.get("/sectors")
def get_sectors() -> list[dict]:
    return to_records(load_table("sector_summary").sort_values("market_cap_rank"))


@app.get("/top-gainers")
def get_top_gainers(sector: Optional[str] = None, limit: int = 15) -> list[dict]:
    df = load_table("top_gainers")
    if sector:
        df = df[df["sector"] == sector.strip()]
    return to_records(df.sort_values("overall_rank").head(max(1, min(limit, 505))))


@app.get("/volume-leaders")
def get_volume_leaders(sector: Optional[str] = None, limit: int = 5) -> list[dict]:
    df = load_table("volume_leaders_by_sector")
    if sector:
        df = df[df["sector"] == sector.strip()]
    df = df[df["sector_volume_rank"] <= max(1, limit)]
    return to_records(df.sort_values(["sector", "sector_volume_rank"]))


@app.get("/stocks/{ticker}")
def get_stock_history(ticker: str, days: int = 252) -> list[dict]:
    sym = ticker.strip().upper()
    df = load_table("daily_returns_sma50")
    sub = df[df["ticker"] == sym].sort_values("date").tail(max(1, min(days, 2000)))
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"Ticker '{sym}' not found")
    return to_records(sub)
