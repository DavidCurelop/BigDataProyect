-- Q4: Average Daily Return % and Daily Volatility by Sector (EMR Hive / Hue / SparkSQL)
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
