# SQLScripts — US 4.1 Descriptive SQL Analytics (Punto 6)

SQL queries answering the 5 business questions over `stocks_db.stocks_enriched` across **Amazon Athena**, **EMR Hive / Hue**, and **SparkSQL**.

> **Note:** Verify exact column names first with `DESCRIBE stocks_db.stocks_enriched;` (especially `date`, `ticker`, `sector`, `close`, `volume`, `market_cap`).

## Folder Layout
- `athena/` — Single-statement Trino/Presto SQL scripts (quotes `"date"` with double quotes for Amazon Athena).
- `emr/` — Hive / Hue / SparkSQL scripts (quotes `` `date` `` with backticks) plus `run_all_emr.sql`.

## 1. Run in Amazon Athena
1. Set query result location to `s3://stock-big-data-bucket/athena-results/`.
2. Select Data source `AwsDataCatalog` and Database `stocks_db`.
3. Open each file in `athena/` one at a time (Athena allows one SQL statement per execution) and run it.

## 2. Run on EMR (Hive, Hue, and SparkSQL)
Upload to S3 (so scripts persist even if the EMR cluster is terminated/cloned) or `scp` directly to the primary node:

```powershell
# Optional: persist in S3
aws s3 sync .\SQLScripts s3://stock-big-data-bucket/scripts/SQLScripts/

# Copy to EMR primary node
scp -i .\labsuser.pem -r .\SQLScripts hadoop@<EMR_PRIMARY_PUBLIC_DNS>:~/SQLScripts
ssh -i .\labsuser.pem hadoop@<EMR_PRIMARY_PUBLIC_DNS>
```

On the EMR primary node:
```bash
# Hive CLI
hive -f ~/SQLScripts/emr/run_all_emr.sql | tee ~/hive_punto6.log

# SparkSQL CLI (with Glue Data Catalog)
spark-sql \
  --conf spark.hadoop.hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory \
  -f ~/SQLScripts/emr/run_all_emr.sql | tee ~/sparksql_punto6.log
```

In **Hue**, open **Query → Editor → Hive** (and **Spark** if enabled), select `stocks_db`, and paste/run each `emr/q*.sql` file individually.
