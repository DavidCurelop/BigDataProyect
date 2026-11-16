# EMRScripts – Glue Data Catalog & EMR Hive/SparkSQL Verification (Punto 5 / US 3.2)

Verifies that `stocks_db.stocks_enriched` (cataloged by AWS Glue Crawler `sp500-trusted-crawler` over `s3://stock-big-data-bucket/trusted/stocks_enriched/`, partitioned by `sector`) is queryable across EMR Hive and SparkSQL.

## Files
- `verify_hive.q` — HiveQL checks (`SHOW DATABASES`, `SHOW TABLES`, `DESCRIBE FORMATTED stocks_enriched`, `SHOW PARTITIONS stocks_enriched`).
- `verify_sparksql.py` — PySpark SQL verification script against the Glue Data Catalog.

## Run on EMR Primary Node
```bash
scp -i labsuser.pem -r EMRScripts hadoop@<EMR_PRIMARY_PUBLIC_DNS>:~/EMRScripts
ssh -i labsuser.pem hadoop@<EMR_PRIMARY_PUBLIC_DNS>

hive -f ~/EMRScripts/verify_hive.q
spark-submit --conf spark.hadoop.hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory ~/EMRScripts/verify_sparksql.py
```
