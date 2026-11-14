from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.error
import urllib.request

import boto3
import pymysql

BASE_DIR = Path(__file__).resolve().parent
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"
RDS_TABLES = ("companies", "fundamentals")


def load_env(env_file: Path) -> None:
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def rows_to_csv_bytes(cols: list[str], rows: list[tuple]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(cols)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


# shortcut: overwrites fixed table keys under raw/rds_companies/ instead of date-partitioning; add dt={run_date}/ if RDS history is needed
def export_rds_tables(s3, bucket: str) -> list[str]:
    conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database="sp500",
        connect_timeout=15,
    )
    symbols: list[str] = []
    try:
        with conn.cursor() as cur:
            for table in RDS_TABLES:
                cur.execute(f"SELECT * FROM {table}")
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                assert len(rows) >= 500, f"{table}: expected >= 500 rows, got {len(rows)}"
                key = f"raw/rds_companies/{table}/{table}.csv"
                s3.put_object(Bucket=bucket, Key=key, Body=rows_to_csv_bytes(cols, rows), ContentType="text/csv")
                print(f"[rds] uploaded {len(rows)} rows -> s3://{bucket}/{key}")
                if table == "companies":
                    sym_idx = cols.index("symbol")
                    symbols = sorted({str(r[sym_idx]).strip().upper() for r in rows if r[sym_idx]})
    finally:
        conn.close()
    return symbols


def sync_ohlcv(bucket: str, ohlcv_dir: Path) -> int:
    assert ohlcv_dir.is_dir(), f"OHLCV directory not found: {ohlcv_dir}"
    csv_count = sum(1 for _ in ohlcv_dir.glob("*.csv"))
    assert csv_count >= 450, f"Expected >= 450 CSV files in {ohlcv_dir}, got {csv_count}"

    # Cron runs with a minimal PATH (/usr/bin:/bin), so probe standard AWS CLI install locations too.
    aws_bin = shutil.which("aws") or next(
        (
            str(p)
            for p in (Path("/usr/local/bin/aws"), Path("/usr/bin/aws"), Path.home() / ".local/bin/aws")
            if p.exists()
        ),
        None,
    )
    assert aws_bin, "aws CLI not found in PATH, /usr/local/bin/aws, or /usr/bin/aws"

    dest = f"s3://{bucket}/raw/ec2_historical_ohlcv/"
    subprocess.run([aws_bin, "s3", "sync", str(ohlcv_dir), dest, "--only-show-errors"], check=True)
    print(f"[ec2] synced {csv_count} CSV files -> {dest}")
    return csv_count


def fetch_latest_quote(ticker: str) -> dict | None:
    req = urllib.request.Request(
        CHART_URL.format(symbol=ticker.replace(".", "-")),
        headers={"User-Agent": "Mozilla/5.0"},
    )
    data = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                return None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                return None
        except (json.JSONDecodeError, ValueError):
            return None
        time.sleep(2**attempt)

    try:
        result = data["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        quote = result["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError):
        return None

    latest: dict | None = None
    for ts, o, h, l, c, v in zip(
        timestamps,
        quote.get("open", []),
        quote.get("high", []),
        quote.get("low", []),
        quote.get("close", []),
        quote.get("volume", []),
    ):
        if None in (ts, o, h, l, c, v):
            continue
        date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        if latest is None or date_str > latest["date"]:
            latest = {
                "date": date_str,
                "ticker": ticker,
                "open": round(float(o), 4),
                "high": round(float(h), 4),
                "low": round(float(l), 4),
                "close": round(float(c), 4),
                "volume": int(v),
            }
    return latest


def upload_yfinance_quotes(s3, bucket: str, symbols: list[str], run_date: str) -> int:
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = [rec for rec in pool.map(fetch_latest_quote, symbols) if rec is not None]
    assert len(records) >= 450, f"Expected >= 450 Yahoo quotes, got {len(records)}"

    ndjson = ("\n".join(json.dumps(r) for r in records) + "\n").encode("utf-8")
    key = f"raw/yfinance_quotes/dt={run_date}/quotes.json"
    s3.put_object(Bucket=bucket, Key=key, Body=ndjson, ContentType="application/x-ndjson")
    print(f"[yfinance] uploaded {len(records)} quotes -> s3://{bucket}/{key}")
    return len(records)


def main() -> None:
    for env_path in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
        load_env(env_path)
    bucket = os.environ["S3_BUCKET"].strip()
    assert bucket, "S3_BUCKET must be set and non-empty"
    ohlcv_dir = Path(os.environ.get("OHLCV_DIR", "/data/ohlcv"))
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== S3 raw ingestion started at {datetime.now(timezone.utc).isoformat()} ===")
    s3 = boto3.client("s3", region_name=region)

    symbols = export_rds_tables(s3, bucket)
    sync_ohlcv(bucket, ohlcv_dir)
    upload_yfinance_quotes(s3, bucket, symbols, run_date)
    print(f"=== S3 raw ingestion completed ({len(symbols)} symbols) ===")


if __name__ == "__main__":
    main()
