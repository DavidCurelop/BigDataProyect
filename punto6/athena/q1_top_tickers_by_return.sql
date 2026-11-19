-- Q1: Top 15 Tickers by Total Return % (Amazon Athena)
WITH ranked AS (
    SELECT
        ticker,
        sector,
        "date",
        close,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY "date" ASC) AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY "date" DESC) AS rn_last
    FROM stocks_db.stocks_enriched
    WHERE close IS NOT NULL
)
SELECT
    ticker,
    MAX(sector) AS sector,
    MIN(CASE WHEN rn_first = 1 THEN "date" END) AS start_date,
    MAX(CASE WHEN rn_last = 1 THEN "date" END) AS end_date,
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
