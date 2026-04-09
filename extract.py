from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv
load_dotenv()

def extract_tpch_tables():
    spark = SparkSession.builder \
    .appName("BenchPress") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0") \
    .getOrCreate()

    # JDBC configuration - read from environment (or .env)
    jdbc_url = os.getenv("TPCH_JDBC_URL")
    jdbc_user = os.getenv("TPCH_JDBC_USER")
    jdbc_password = os.getenv("TPCH_JDBC_PASSWORD")
    jdbc_driver = os.getenv("TPCH_JDBC_DRIVER", "com.mysql.cj.jdbc.Driver")
    use_jdbc = os.getenv("TPCH_USE_JDBC", "false").lower() == "true"

    # List of all TPC-H tables
    table_names = ["lineitem", "orders", "customer", "nation", "region",
                   "part", "supplier", "partsupp"]
    tables = {}

    for table in table_names:
        if use_jdbc:
            if not all([jdbc_url, jdbc_user, jdbc_password]):
                raise ValueError("JDBC connection parameters missing. Check .env file.")
            df = spark.read.format("jdbc").options(
                url=jdbc_url,
                dbtable=table,
                user=jdbc_user,
                password=jdbc_password,
                driver=jdbc_driver
            ).load()
        else:
            print(f"Table not found in JDBC mode, skipping: {table}")
        tables[table] = df

    return spark, tables