-- Q3: Sector Market-Cap Ranking (EMR Hive / Hue / SparkSQL)
-- Deduplicate market_cap per ticker first because daily OHLCV rows repeat company fundamentals.
WITH per_ticker AS (
    SELECT
        ticker,
        sector,
        MAX(market_cap) AS market_cap
    FROM stocks_db.stocks_enriched
    WHERE market_cap IS NOT NULL
    GROUP BY ticker, sector
),
sector_totals AS (
    SELECT
        sector,
        COUNT(*) AS num_companies,
        SUM(market_cap) AS sector_market_cap,
        ROUND(AVG(market_cap), 2) AS avg_company_market_cap
    FROM per_ticker
    GROUP BY sector
)
SELECT
    sector,
    num_companies,
    sector_market_cap,
    avg_company_market_cap,
    RANK() OVER (ORDER BY sector_market_cap DESC) AS market_cap_rank
FROM sector_totals
ORDER BY market_cap_rank ASC;
