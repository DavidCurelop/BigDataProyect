-- Q5: 50-Day Simple Moving Average (SMA-50) Latest Snapshot (EMR Hive / Hue / SparkSQL)
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
