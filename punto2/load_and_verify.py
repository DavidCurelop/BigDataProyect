import csv
import io
import os
from pathlib import Path
import urllib.request

import pymysql

COMPANIES_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
FUNDAMENTALS_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies-financials/main/data/constituents-financials.csv"
BASE_DIR = Path(__file__).resolve().parent


def fetch_csv(url: str) -> list[dict[str, str]]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return list(csv.DictReader(io.StringIO(resp.read().decode("utf-8"))))


def num(val: str | None, cast=float):
    if val is None or not val.strip():
        return None
    return cast(float(val))


def run_sql_statements(cur, sql_text: str) -> list[list[tuple]]:
    results = []
    for stmt in (s.strip() for s in sql_text.split(";")):
        if not stmt:
            continue
        cur.execute(stmt)
        if cur.description:
            results.append(([d[0] for d in cur.description], cur.fetchall()))
    return results


def main() -> None:
    env_file = BASE_DIR.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    host = os.environ["DB_HOST"]
    port = int(os.environ.get("DB_PORT", "3306"))
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    conn = pymysql.connect(host=host, port=port, user=user, password=password, autocommit=True)
    try:
        with conn.cursor() as cur:
            run_sql_statements(cur, (BASE_DIR / "schema.sql").read_text(encoding="utf-8"))

            companies = fetch_csv(COMPANIES_URL)
            cur.executemany(
                """
                INSERT INTO companies
                    (symbol, security, gics_sector, gics_sub_industry, headquarters_location, date_added, cik, founded)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    security = VALUES(security),
                    gics_sector = VALUES(gics_sector),
                    gics_sub_industry = VALUES(gics_sub_industry),
                    headquarters_location = VALUES(headquarters_location),
                    date_added = VALUES(date_added),
                    cik = VALUES(cik),
                    founded = VALUES(founded)
                """,
                [
                    (
                        r["Symbol"],
                        r["Security"],
                        r["GICS Sector"] or None,
                        r["GICS Sub-Industry"] or None,
                        r["Headquarters Location"] or None,
                        r["Date added"] or None,
                        num(r["CIK"], int),
                        r["Founded"] or None,
                    )
                    for r in companies
                ],
            )

            fundamentals = fetch_csv(FUNDAMENTALS_URL)
            
            cur.executemany(
                "INSERT IGNORE INTO companies (symbol, security, gics_sector) VALUES (%s, %s, %s)",
                [(r["Symbol"], r["Name"] or r["Symbol"], r["Sector"] or None) for r in fundamentals],
            )
            cur.executemany(
                """
                INSERT INTO fundamentals
                    (symbol, name, sector, price, price_earnings, dividend_yield, earnings_share,
                     week_52_low, week_52_high, market_cap, ebitda, price_sales, price_book, sec_filings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    sector = VALUES(sector),
                    price = VALUES(price),
                    price_earnings = VALUES(price_earnings),
                    dividend_yield = VALUES(dividend_yield),
                    earnings_share = VALUES(earnings_share),
                    week_52_low = VALUES(week_52_low),
                    week_52_high = VALUES(week_52_high),
                    market_cap = VALUES(market_cap),
                    ebitda = VALUES(ebitda),
                    price_sales = VALUES(price_sales),
                    price_book = VALUES(price_book),
                    sec_filings = VALUES(sec_filings)
                """,
                [
                    (
                        r["Symbol"],
                        r["Name"] or None,
                        r["Sector"] or None,
                        num(r["Price"]),
                        num(r["Price/Earnings"]),
                        num(r["Dividend Yield"]),
                        num(r["Earnings/Share"]),
                        num(r["52 Week Low"]),
                        num(r["52 Week High"]),
                        num(r["Market Cap"], int),
                        num(r["EBITDA"], int),
                        num(r["Price/Sales"]),
                        num(r["Price/Book"]),
                        r["SEC Filings"] or None,
                    )
                    for r in fundamentals
                ],
            )

            outputs = run_sql_statements(cur, (BASE_DIR / "verify.sql").read_text(encoding="utf-8"))
            for cols, rows in outputs:
                print(cols)
                for row in rows:
                    print(row)

            total_companies = outputs[0][1][0][0]
            total_fundamentals = outputs[1][1][0][0]
            assert total_companies >= 500, f"Expected >= 500 companies, got {total_companies}"
            assert total_fundamentals >= 500, f"Expected >= 500 fundamentals, got {total_fundamentals}"
    finally:
        conn.close()


if __name__ == "__main__":
    main()
