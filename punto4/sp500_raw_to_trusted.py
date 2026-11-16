import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsgluedq.transforms import EvaluateDataQuality
from awsglue.dynamicframe import DynamicFrame
from awsglue import DynamicFrame
import gs_derived
from pyspark.sql import functions as SqlFuncs

def sparkUnion(glueContext, unionType, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql("(select * from source1) UNION " + unionType + " (select * from source2)")
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Default ruleset used by all target nodes with data quality enabled
DEFAULT_DATA_QUALITY_RULESET = """
    Rules = [
        ColumnCount > 0
    ]
"""

# Script generated for node S3_Fundamentals
S3_Fundamentals_node1794711365665 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://stock-big-data-bucket/raw/rds_companies/fundamentals/"], "recurse": True}, transformation_ctx="S3_Fundamentals_node1794711365665")

# Script generated for node S3_YFinance_Quotes
S3_YFinance_Quotes_node1794710494268 = glueContext.create_dynamic_frame.from_options(format_options={"multiLine": "false"}, connection_type="s3", format="json", connection_options={"paths": ["s3://stock-big-data-bucket/raw/yfinance_quotes/"], "recurse": True}, transformation_ctx="S3_YFinance_Quotes_node1794710494268")

# Script generated for node S3_Historical_OHLCV
S3_Historical_OHLCV_node1794710252774 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://stock-big-data-bucket/raw/ec2_historical_ohlcv/"], "recurse": True}, transformation_ctx="S3_Historical_OHLCV_node1794710252774")

# Script generated for node S3_Companies
S3_Companies_node1794711240022 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://stock-big-data-bucket/raw/rds_companies/companies/"], "recurse": True}, transformation_ctx="S3_Companies_node1794711240022")

# Script generated for node Prep_Fundamentals
Prep_Fundamentals_node1794711442281 = ApplyMapping.apply(frame=S3_Fundamentals_node1794711365665, mappings=[("symbol", "string", "fund_symbol", "string"), ("name", "string", "name", "string"), ("sector", "string", "fund_sector", "string"), ("price", "string", "price", "double"), ("price_earnings", "string", "price_earnings", "double"), ("dividend_yield", "string", "dividend_yield", "double"), ("earnings_share", "string", "earnings_share", "double"), ("week_52_low", "string", "week_52_low", "double"), ("week_52_high", "string", "week_52_high", "double"), ("market_cap", "string", "market_cap", "bigint"), ("ebitda", "string", "ebitda", "bigint"), ("price_sales", "string", "price_sales", "double"), ("price_book", "string", "price_book", "double"), ("sec_filings", "string", "sec_filings", "string")], transformation_ctx="Prep_Fundamentals_node1794711442281")

# Script generated for node Align_YFinance_Schema
Align_YFinance_Schema_node1794710581350 = ApplyMapping.apply(frame=S3_YFinance_Quotes_node1794710494268, mappings=[("date", "string", "date", "string"), ("ticker", "string", "ticker", "string"), ("open", "double", "open", "double"), ("high", "double", "high", "double"), ("low", "double", "low", "double"), ("close", "double", "close", "double"), ("volume", "int", "volume", "int")], transformation_ctx="Align_YFinance_Schema_node1794710581350")

# Script generated for node Align_Historical_Schema
Align_Historical_Schema_node1794710431245 = ApplyMapping.apply(frame=S3_Historical_OHLCV_node1794710252774, mappings=[("date", "string", "date", "string"), ("ticker", "string", "ticker", "string"), ("open", "string", "open", "double"), ("high", "string", "high", "double"), ("low", "string", "low", "double"), ("close", "string", "close", "double"), ("volume", "string", "volume", "bigint")], transformation_ctx="Align_Historical_Schema_node1794710431245")

# Script generated for node Join_Companies_Fundamentals
S3_Companies_node1794711240022DF = S3_Companies_node1794711240022.toDF()
Prep_Fundamentals_node1794711442281DF = Prep_Fundamentals_node1794711442281.toDF()
Join_Companies_Fundamentals_node1794711599782 = DynamicFrame.fromDF(S3_Companies_node1794711240022DF.join(Prep_Fundamentals_node1794711442281DF, (S3_Companies_node1794711240022DF['symbol'] == Prep_Fundamentals_node1794711442281DF['fund_symbol']), "left"), glueContext, "Join_Companies_Fundamentals_node1794711599782")

# Script generated for node Union_OHLCV
Union_OHLCV_node1794710651784 = sparkUnion(glueContext, unionType = "ALL", mapping = {"source1": Align_Historical_Schema_node1794710431245, "source2": Align_YFinance_Schema_node1794710581350}, transformation_ctx = "Union_OHLCV_node1794710651784")

# Script generated for node Derive_Symbol_Clean
Derive_Symbol_Clean_node1794711721915 = Join_Companies_Fundamentals_node1794711599782.gs_derived(colName="symbol_clean", expr="upper(trim(symbol))")

# Script generated for node Derive_Ticker_Clean
Derive_Ticker_Clean_node1794710739880 = Union_OHLCV_node1794710651784.gs_derived(colName="ticker_clean", expr="upper(trim(ticker))")

# Script generated for node Derive_DateAdded_Clean
Derive_DateAdded_Clean_node1794711759888 = Derive_Symbol_Clean_node1794711721915.gs_derived(colName="date_added_clean", expr="date_format(to_date(substring(trim(date_added), 1, 10), 'yyyy-MM-dd'), 'yyyy-MM-dd')")

# Script generated for node Derive_Date_Clean
Derive_Date_Clean_node1794710813029 = Derive_Ticker_Clean_node1794710739880.gs_derived(colName="date_clean", expr="date_format(to_date(trim(date), 'yyyy-MM-dd'), 'yyyy-MM-dd')")

# Script generated for node Derive_Unified_Sector
Derive_Unified_Sector_node1794711831607 = Derive_DateAdded_Clean_node1794711759888.gs_derived(colName="sector", expr="coalesce(nullif(trim(fund_sector), ''), nullif(trim(gics_sector), ''), 'Unknown')")

# Script generated for node Clean_OHLCV_Schema
Clean_OHLCV_Schema_node1794710993204 = ApplyMapping.apply(frame=Derive_Date_Clean_node1794710813029, mappings=[("open", "double", "open", "double"), ("high", "double", "high", "double"), ("low", "double", "low", "double"), ("close", "double", "close", "double"), ("volume", "long", "volume", "long"), ("ticker_clean", "string", "ticker", "string"), ("date_clean", "string", "date", "string")], transformation_ctx="Clean_OHLCV_Schema_node1794710993204")

# Script generated for node Finalize_Metadata_Schema
Finalize_Metadata_Schema_node1794711878627 = ApplyMapping.apply(frame=Derive_Unified_Sector_node1794711831607, mappings=[("security", "string", "security", "string"), ("gics_sector", "string", "gics_sector", "string"), ("gics_sub_industry", "string", "gics_sub_industry", "string"), ("headquarters_location", "string", "headquarters_location", "string"), ("cik", "string", "cik", "string"), ("founded", "string", "founded", "string"), ("name", "string", "name", "string"), ("price", "double", "price", "double"), ("price_earnings", "double", "price_earnings", "double"), ("dividend_yield", "double", "dividend_yield", "double"), ("earnings_share", "double", "earnings_share", "double"), ("week_52_low", "double", "week_52_low", "double"), ("week_52_high", "double", "week_52_high", "double"), ("market_cap", "long", "market_cap", "long"), ("ebitda", "long", "ebitda", "long"), ("price_sales", "double", "price_sales", "double"), ("price_book", "double", "price_book", "double"), ("sec_filings", "string", "sec_filings", "string"), ("symbol_clean", "string", "symbol", "string"), ("date_added_clean", "string", "date_added", "string"), ("sector", "string", "sector", "string")], transformation_ctx="Finalize_Metadata_Schema_node1794711878627")

# Script generated for node Deduplicate_OHLCV
Deduplicate_OHLCV_node1794711048050 =  DynamicFrame.fromDF(Clean_OHLCV_Schema_node1794710993204.toDF().dropDuplicates(["ticker", "date"]), glueContext, "Deduplicate_OHLCV_node1794711048050")

# Script generated for node Join_Enriched_Stocks
Deduplicate_OHLCV_node1794711048050DF = Deduplicate_OHLCV_node1794711048050.toDF()
Finalize_Metadata_Schema_node1794711878627DF = Finalize_Metadata_Schema_node1794711878627.toDF()
Join_Enriched_Stocks_node1794711987516 = DynamicFrame.fromDF(Deduplicate_OHLCV_node1794711048050DF.join(Finalize_Metadata_Schema_node1794711878627DF, (Deduplicate_OHLCV_node1794711048050DF['ticker'] == Finalize_Metadata_Schema_node1794711878627DF['symbol']), "left"), glueContext, "Join_Enriched_Stocks_node1794711987516")

# Script generated for node Final_Output_Schema
Final_Output_Schema_node1794712092211 = ApplyMapping.apply(frame=Join_Enriched_Stocks_node1794711987516, mappings=[("open", "double", "open", "double"), ("high", "double", "high", "double"), ("low", "double", "low", "double"), ("close", "double", "close", "double"), ("volume", "long", "volume", "long"), ("ticker", "string", "ticker", "string"), ("date", "string", "date", "string"), ("security", "string", "security", "string"), ("gics_sector", "string", "gics_sector", "string"), ("gics_sub_industry", "string", "gics_sub_industry", "string"), ("headquarters_location", "string", "headquarters_location", "string"), ("cik", "string", "cik", "string"), ("founded", "string", "founded", "string"), ("name", "string", "name", "string"), ("price", "double", "price", "double"), ("price_earnings", "double", "price_earnings", "double"), ("dividend_yield", "double", "dividend_yield", "double"), ("earnings_share", "double", "earnings_share", "double"), ("week_52_low", "double", "week_52_low", "double"), ("week_52_high", "double", "week_52_high", "double"), ("market_cap", "long", "market_cap", "long"), ("ebitda", "long", "ebitda", "long"), ("price_sales", "double", "price_sales", "double"), ("price_book", "double", "price_book", "double"), ("sec_filings", "string", "sec_filings", "string"), ("date_added_clean", "string", "date_added_clean", "string"), ("sector", "string", "sector", "string")], transformation_ctx="Final_Output_Schema_node1794712092211")

# Script generated for node S3_Trusted_Parquet
EvaluateDataQuality().process_rows(frame=Final_Output_Schema_node1794712092211, ruleset=DEFAULT_DATA_QUALITY_RULESET, publishing_options={"dataQualityEvaluationContext": "EvaluateDataQuality_node1794710082652", "enableDataQualityResultsPublishing": True}, additional_options={"dataQualityResultsPublishing.strategy": "BEST_EFFORT", "observations.scope": "ALL"})
S3_Trusted_Parquet_node1794712205328 = glueContext.write_dynamic_frame.from_options(frame=Final_Output_Schema_node1794712092211, connection_type="s3", format="glueparquet", connection_options={"path": "s3://stock-big-data-bucket/trusted/stocks_enriched/", "partitionKeys": ["sector"]}, format_options={"compression": "snappy"}, transformation_ctx="S3_Trusted_Parquet_node1794712205328")

job.commit()