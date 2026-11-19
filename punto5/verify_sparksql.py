from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("VerifyGlueCatalog").enableHiveSupport().getOrCreate()
spark.sql("USE stocks_db")
spark.sql("SHOW TABLES").show(truncate=False)
spark.sql("DESCRIBE stocks_enriched").show(100, truncate=False)
spark.sql("SHOW PARTITIONS stocks_enriched").show(50, truncate=False)
spark.stop()