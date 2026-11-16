-- Run all 5 US 4.1 descriptive analytical queries sequentially in EMR Hive or SparkSQL
USE stocks_db;

-- Q1: Top 15 Tickers by Total Return %
WITH ranked AS (
    SELECT
        ticker,
        sector,
        `date`,
        close,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY `date` ASC) AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY `date` DESC) AS rn_last
    FROM stocks_db.stocks_enriched
    WHERE close IS NOT NULL
)
SELECT
    ticker,
    MAX(sector) AS sector,
    MIN(CASE WHEN rn_first = 1 THEN `date` END) AS start_date,
    MAX(CASE WHEN rn_last = 1 THEN `date` END) AS end_date,
    ROUND(MAX(CASE WHEN rn_first = 1 THEN close END), 4) AS first_close,
    ROUND(MAX(CASE WHEN rn_last = 1 THEN close END), 4) AS last_close,
    ROUND(
        ((MAX(CASE WHEN rn_last = 1 THEN close END) - MAX(CASE WHEN rn_first = 1 THEN close END))
         / NULLIF(MAX(CASE WHEN rn_first = 1 THEN close END), 0)) * 100.0,
        2
    ) AS total_return_pct
FROM ranked
WHERE rn_first = 1 OR rn_last = 1
GROUP BY ticker
HAVING MAX(CASE WHEN rn_first = 1 THEN close END) > 0
ORDER BY total_return_pct DESC
LIMIT 15;

-- Q2: Average Daily Trading Volume by Sector
SELECT
    sector,
    COUNT(DISTINCT ticker) AS num_tickers,
    COUNT(*) AS trading_rows,
    ROUND(AVG(volume), 2) AS avg_daily_volume,
    SUM(volume) AS total_volume
FROM stocks_db.stocks_enriched
WHERE volume IS NOT NULL
GROUP BY sector
ORDER BY avg_daily_volume DESC;

-- Q3: Sector Market-Cap Ranking
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

-- Q4: Average Daily Return % and Daily Volatility by Sector
WITH lagged AS (
    SELECT
        ticker,
        sector,
        `date`,
        close,
        LAG(close) OVER (PARTITION BY ticker ORDER BY `date`) AS prev_close
    FROM stocks_db.stocks_enriched
    WHERE close IS NOT NULL
),
daily_returns AS (
    SELECT
        ticker,
        sector,
        `date`,
        ((close - prev_close) / NULLIF(prev_close, 0)) * 100.0 AS daily_return_pct
    FROM lagged
    WHERE prev_close IS NOT NULL AND prev_close > 0
)
SELECT
    sector,
    COUNT(*) AS return_observations,
    ROUND(AVG(daily_return_pct), 4) AS avg_daily_return_pct,
    ROUND(STDDEV_SAMP(daily_return_pct), 4) AS daily_volatility_pct
FROM daily_returns
GROUP BY sector
ORDER BY daily_volatility_pct DESC;

-- Q5: 50-Day Simple Moving Average (SMA-50) Latest Snapshot
WITH sma AS (
    SELECT
        ticker,
        sector,
        `date`,
        close,
        AVG(close) OVER (
            PARTITION BY ticker
            ORDER BY `date`
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ) AS sma_50,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY `date` DESC) AS rn
    FROM stocks_db.stocks_enriched
    WHERE close IS NOT NULL
)
SELECT
    ticker,
    sector,
    `date` AS latest_date,
    ROUND(close, 4) AS latest_close,
    ROUND(sma_50, 4) AS sma_50,
    ROUND(((close - sma_50) / NULLIF(sma_50, 0)) * 100.0, 2) AS pct_vs_sma50
FROM sma
WHERE rn = 1
ORDER BY pct_vs_sma50 DESC
LIMIT 20;
