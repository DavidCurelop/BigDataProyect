import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s3_ingestion


class TestS3Ingestion(unittest.TestCase):
    def test_rows_to_csv_bytes(self) -> None:
        raw = s3_ingestion.rows_to_csv_bytes(["symbol", "price"], [("AAPL", 190.5)])
        self.assertEqual(raw.decode("utf-8"), "symbol,price\r\nAAPL,190.5\r\n")

    def test_fetch_latest_quote_picks_newest_valid_bar(self) -> None:
        payload = {
            "chart": {
                "result": [
                    {
                        "timestamp": [1731369600, 1731456000, 1731542400],
                        "indicators": {
                            "quote": [
                                {
                                    "open": [100.0, 101.0, None],
                                    "high": [102.0, 103.0, None],
                                    "low": [99.0, 100.5, None],
                                    "close": [101.5, 102.25, None],
                                    "volume": [1000, 2000, None],
                                }
                            ]
                        },
                    }
                ]
            }
        }
        resp = MagicMock()
        resp.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
        with patch("s3_ingestion.urllib.request.urlopen", return_value=resp):
            quote = s3_ingestion.fetch_latest_quote("BRK.B")
        self.assertEqual(quote["ticker"], "BRK.B")
        self.assertEqual(quote["date"], "2024-11-13")
        self.assertEqual(quote["close"], 102.25)
        self.assertEqual(quote["volume"], 2000)

    def test_export_rds_and_sync_ohlcv(self) -> None:
        s3 = MagicMock()
        cur = MagicMock()
        cur.description = [("symbol",), ("name",)]
        cur.fetchall.return_value = [(f"T{i}", f"Co {i}") for i in range(500)]
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur

        with (
            patch.dict("os.environ", {"DB_HOST": "localhost", "DB_USER": "u", "DB_PASSWORD": "p"}),
            patch("s3_ingestion.pymysql.connect", return_value=conn),
        ):
            symbols = s3_ingestion.export_rds_tables(s3, "my-bucket")

        self.assertEqual(len(symbols), 500)
        keys = [c.kwargs["Key"] for c in s3.put_object.call_args_list]
        self.assertEqual(
            keys,
            ["raw/rds_companies/companies/companies.csv", "raw/rds_companies/fundamentals/fundamentals.csv"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            for i in range(450):
                (Path(tmp) / f"T{i}.csv").write_text("date,ticker\n", encoding="utf-8")
            with (
                patch("s3_ingestion.shutil.which", return_value="/usr/local/bin/aws"),
                patch("s3_ingestion.subprocess.run") as run_mock,
            ):
                count = s3_ingestion.sync_ohlcv("my-bucket", Path(tmp))
        self.assertEqual(count, 450)
        run_mock.assert_called_once_with(
            ["/usr/local/bin/aws", "s3", "sync", tmp, "s3://my-bucket/raw/ec2_historical_ohlcv/", "--only-show-errors"],
            check=True,
        )

    def test_upload_yfinance_quotes_writes_ndjson(self) -> None:
        s3 = MagicMock()
        sample = {"date": "2026-11-13", "ticker": "AAPL", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10}
        with patch("s3_ingestion.fetch_latest_quote", side_effect=lambda t: {**sample, "ticker": t}):
            count = s3_ingestion.upload_yfinance_quotes(s3, "my-bucket", [f"T{i}" for i in range(450)], "2026-11-14")
        self.assertEqual(count, 450)
        kwargs = s3.put_object.call_args.kwargs
        self.assertEqual(kwargs["Key"], "raw/yfinance_quotes/dt=2026-11-14/quotes.json")
        lines = kwargs["Body"].decode("utf-8").splitlines()
        self.assertEqual(len(lines), 450)
        self.assertEqual(json.loads(lines[0])["ticker"], "T0")


if __name__ == "__main__":
    unittest.main()
