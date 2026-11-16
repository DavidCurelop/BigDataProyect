import io
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import api
import dashboard


def _parquet_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


class TestPunto8(unittest.TestCase):
    def setUp(self) -> None:
        api.load_table.cache_clear()
        self.tables = {
            "daily_returns_sma50": pd.DataFrame(
                [
                    {"ticker": "AAPL", "sector": "IT", "date": pd.Timestamp("2026-11-12"), "close": 220.0, "volume": 100, "prev_close": None, "daily_return_pct": None, "sma_50": 210.0, "pct_vs_sma50": 4.76},
                    {"ticker": "AAPL", "sector": "IT", "date": pd.Timestamp("2026-11-13"), "close": 225.0, "volume": 150, "prev_close": 220.0, "daily_return_pct": 2.27, "sma_50": 211.0, "pct_vs_sma50": 6.64},
                ]
            ),
            "sector_summary": pd.DataFrame(
                [{"sector": "IT", "num_tickers": 1, "trading_rows": 2, "avg_daily_volume": 125.0, "total_volume": 250, "num_companies": 1, "sector_market_cap": 3.4e12, "avg_company_market_cap": 3.4e12, "return_observations": 1, "avg_daily_return_pct": 2.27, "daily_volatility_pct": 0.5, "market_cap_rank": 1}]
            ),
            "top_gainers": pd.DataFrame(
                [{"ticker": "AAPL", "sector": "IT", "start_date": "2026-11-12", "end_date": "2026-11-13", "first_close": 220.0, "last_close": 225.0, "total_return_pct": 2.27, "overall_rank": 1, "sector_rank": 1}]
            ),
            "volume_leaders_by_sector": pd.DataFrame(
                [{"sector": "IT", "ticker": "AAPL", "trading_days": 2, "avg_daily_volume": 125.0, "max_daily_volume": 150, "total_volume": 250, "sector_volume_rank": 1}]
            ),
        }

        s3 = MagicMock()
        s3.list_objects_v2.side_effect = lambda Bucket, Prefix: {"Contents": [{"Key": f"{Prefix}part-00000.parquet"}]}
        s3.get_object.side_effect = lambda Bucket, Key: {"Body": io.BytesIO(_parquet_bytes(self.tables[Key.split("/")[-2]]))}
        self.s3_patch = patch("api.boto3.client", return_value=s3)
        self.s3_patch.start()

    def tearDown(self) -> None:
        self.s3_patch.stop()
        api.load_table.cache_clear()

    def test_api_endpoints_and_nan_json(self) -> None:
        self.assertEqual(api.health()["tables"]["daily_returns_sma50"], 2)
        rows = api.get_stock_history("aapl")
        json.dumps(rows, allow_nan=False)
        self.assertEqual(rows[0]["date"], "2026-11-12")
        self.assertIsNone(rows[0]["daily_return_pct"])

        with self.assertRaises(HTTPException) as ctx:
            api.get_stock_history("MISSING")
        self.assertEqual(ctx.exception.status_code, 404)

        self.assertEqual(api.get_sectors()[0]["market_cap_rank"], 1)
        self.assertEqual(api.get_top_gainers()[0]["ticker"], "AAPL")
        self.assertEqual(api.get_volume_leaders()[0]["sector_volume_rank"], 1)

    def test_dashboard_fetch_api(self) -> None:
        resp = MagicMock()
        resp.__enter__.return_value.read.return_value = json.dumps([{"ticker": "AAPL"}]).encode("utf-8")
        with patch("dashboard.urllib.request.urlopen", return_value=resp) as open_mock:
            df = dashboard.fetch_api("/top-gainers", {"limit": 15, "sector": None})
        self.assertEqual(df.iloc[0]["ticker"], "AAPL")
        self.assertTrue(open_mock.call_args.args[0].endswith("/top-gainers?limit=15"))


if __name__ == "__main__":
    unittest.main()
