from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

COMPANIES_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d"
EXPECTED_HEADER = ["date", "ticker", "open", "high", "low", "close", "volume"]
OHLCV_DIR = Path(os.environ.get("OHLCV_DIR", "/data/ohlcv"))


def fetch_symbols() -> list[str]:
    with urllib.request.urlopen(COMPANIES_URL, timeout=30) as resp:
        rows = csv.DictReader(io.StringIO(resp.read().decode("utf-8")))
        return sorted({r["Symbol"].strip().upper() for r in rows if r.get("Symbol") and r["Symbol"].strip()})


# shortcut: fetches 1y daily bars from Yahoo v8 chart endpoint without retry backoff, add exponential backoff if rate-limited
def fetch_ohlcv(ticker: str) -> tuple[str, list[tuple]]:
    yahoo_sym = ticker.replace(".", "-")
    req = urllib.request.Request(
        CHART_URL.format(symbol=yahoo_sym),
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result = data["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        quote = result["indicators"]["quote"][0]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        return ticker, []

    by_date: dict[str, tuple] = {}
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
        by_date[date_str] = (
            date_str,
            ticker,
            round(float(o), 4),
            round(float(h), 4),
            round(float(l), 4),
            round(float(c), 4),
            int(v),
        )
    return ticker, [by_date[d] for d in sorted(by_date)]


def stage_files(ohlcv_dir: Path) -> None:
    ohlcv_dir.mkdir(parents=True, exist_ok=True)
    symbols = fetch_symbols()
    with ThreadPoolExecutor(max_workers=16) as pool:
        for ticker, rows in pool.map(fetch_ohlcv, symbols):
            if not rows:
                continue
            with (ohlcv_dir / f"{ticker}.csv").open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(EXPECTED_HEADER)
                writer.writerows(rows)


def verify_files(ohlcv_dir: Path) -> None:
    csv_files = sorted(ohlcv_dir.glob("*.csv"))
    total_rows = 0
    min_date: str | None = None
    max_date: str | None = None

    for path in csv_files:
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            assert header == EXPECTED_HEADER, f"{path.name}: unexpected header {header}"
            for row in reader:
                assert len(row) == 7, f"{path.name}: expected 7 columns, got {len(row)}"
                date_str, ticker, o, h, l, c, v = row
                datetime.strptime(date_str, "%Y-%m-%d")
                assert ticker and ticker == path.stem, f"{path.name}: ticker mismatch {ticker!r}"
                float(o)
                float(h)
                float(l)
                float(c)
                int(v)
                total_rows += 1
                if min_date is None or date_str < min_date:
                    min_date = date_str
                if max_date is None or date_str > max_date:
                    max_date = date_str

    total_files = len(csv_files)
    print(f"total_files={total_files} total_rows={total_rows} min_date={min_date} max_date={max_date}")
    if csv_files:
        sample_path = ohlcv_dir / "AAPL.csv"
        if not sample_path.exists():
            sample_path = csv_files[0]
        print(f"sample_file={sample_path.name}")
        with sample_path.open("r", newline="", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 6:
                    break
                print(line.rstrip("\r\n"))

    assert total_files >= 450, f"Expected >= 450 CSV files, got {total_files}"
    assert total_rows >= 100000, f"Expected >= 100000 total rows, got {total_rows}"


def main() -> None:
    stage_files(OHLCV_DIR)
    verify_files(OHLCV_DIR)


if __name__ == "__main__":
    main()
