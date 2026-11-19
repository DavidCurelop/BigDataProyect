-- Q2: Average Daily Trading Volume by Sector (EMR Hive / Hue / SparkSQL)
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
