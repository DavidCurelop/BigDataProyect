# Punto 5 – SQL Catalogación: AWS Glue Data Catalog & EMR Hive/SparkSQL (US 3.2)

Catalogs `s3://stock-big-data-bucket/trusted/stocks_enriched/` (Snappy Parquet partitioned by `sector`) into `stocks_db.stocks_enriched` using AWS Glue Crawler `sp500-trusted-crawler`, and verifies table metadata across EMR Hive and SparkSQL.

## Files
- [`verify_hive.q`](verify_hive.q) — HiveQL checks (`SHOW DATABASES`, `SHOW TABLES`, `DESCRIBE FORMATTED stocks_enriched`, `SHOW PARTITIONS stocks_enriched`).
- [`verify_sparksql.py`](verify_sparksql.py) — PySpark SQL verification script against the Glue Data Catalog.

## 1. AWS Glue Crawler (`sp500-trusted-crawler`)
1. In **AWS Glue → Crawlers**, configure `sp500-trusted-crawler` with:
   - **Data source:** `s3://stock-big-data-bucket/trusted/stocks_enriched/`
   - **IAM role:** `LabRole`
   - **Target database:** `stocks_db` (table `stocks_enriched`, partition column `sector`)
2. Run the crawler and verify `stocks_db.stocks_enriched` appears in **AWS Glue → Data Catalog → Tables**.

## 2. Run Verification on EMR Primary Node
Ensure the EMR cluster is launched with Glue Data Catalog metadata enabled for Hive and Spark:
```bash
scp -i labsuser.pem -r punto5 hadoop@<EMR_PRIMARY_PUBLIC_DNS>:~/punto5
ssh -i labsuser.pem hadoop@<EMR_PRIMARY_PUBLIC_DNS>

hive -f ~/punto5/verify_hive.q
spark-submit --conf spark.hadoop.hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory ~/punto5/verify_sparksql.py
```
