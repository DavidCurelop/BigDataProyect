CREATE DATABASE IF NOT EXISTS sp500;
USE sp500;

CREATE TABLE IF NOT EXISTS companies (
    symbol VARCHAR(16) PRIMARY KEY,
    security VARCHAR(255) NOT NULL,
    gics_sector VARCHAR(128),
    gics_sub_industry VARCHAR(255),
    headquarters_location VARCHAR(255),
    date_added VARCHAR(32),
    cik INT,
    founded VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS fundamentals (
    symbol VARCHAR(16) PRIMARY KEY,
    name VARCHAR(255),
    sector VARCHAR(128),
    price DECIMAL(12, 4),
    price_earnings DECIMAL(12, 4),
    dividend_yield DECIMAL(12, 6),
    earnings_share DECIMAL(12, 4),
    week_52_low DECIMAL(12, 4),
    week_52_high DECIMAL(12, 4),
    market_cap BIGINT,
    ebitda BIGINT,
    price_sales DECIMAL(12, 6),
    price_book DECIMAL(12, 4),
    sec_filings VARCHAR(512),
    CONSTRAINT fk_fundamentals_company FOREIGN KEY (symbol) REFERENCES companies(symbol)
);
