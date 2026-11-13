USE sp500;
SELECT COUNT(*) AS total_companies FROM companies;
SELECT COUNT(*) AS total_fundamentals FROM fundamentals;
SELECT c.symbol, c.security, c.gics_sector, f.price, f.price_earnings, f.market_cap
FROM companies c
JOIN fundamentals f ON c.symbol = f.symbol
ORDER BY f.market_cap DESC
LIMIT 10;
