from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

load_dotenv()

def extract_tpch_tables():
    # Memory tuned for ~10GB data
    spark = SparkSession.builder \
        .appName("BenchPress") \
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0,"
                "com.datastax.spark:spark-cassandra-connector_2.12:3.5.0,"
                "com.github.jnr:jnr-posix:3.1.15,"
                "com.mysql:mysql-connector-j:8.0.33") \
        .config("spark.cassandra.connection.host", os.getenv("CASSANDRA_HOST", "localhost")) \
        .config("spark.cassandra.connection.port", os.getenv("CASSANDRA_PORT", "9042")) \
        .config("spark.cassandra.output.consistency.level", "ONE") \
        .config("spark.driver.memory", "6g") \
        .config("spark.executor.memory", "6g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.memory.offHeap.enabled", "true") \
        .config("spark.memory.offHeap.size", "4g") \
        .config("spark.cassandra.query.retry.count", "30") \
        .config("spark.cassandra.output.batch.size.rows", "200") \
        .config("spark.cassandra.output.concurrent.writes", "1") \
        .config("spark.cassandra.output.throughputMBPerSec", "1") \
        .config("spark.cassandra.output.batch.grouping.key", "partition") \
        .getOrCreate()

    # JDBC configuration
    jdbc_url_base = os.getenv("TPCH_JDBC_URL")
    jdbc_user = os.getenv("TPCH_JDBC_USER")
    jdbc_password = os.getenv("TPCH_JDBC_PASSWORD")
    jdbc_driver = os.getenv("TPCH_JDBC_DRIVER", "com.mysql.cj.jdbc.Driver")
    use_jdbc = os.getenv("TPCH_USE_JDBC", "false").lower() == "true"

    # Build JDBC URL with useCursorFetch for streaming
    if use_jdbc and jdbc_url_base:
        separator = '&' if '?' in jdbc_url_base else '?'
        jdbc_url = f"{jdbc_url_base}{separator}useCursorFetch=true"
    else:
        jdbc_url = jdbc_url_base

    # Partition config – reduced parallelism to avoid connection storms
    table_partition_config = {
        "lineitem": {"key": "l_orderkey", "lower": 1, "upper": 60000000, "partitions": 200},
        "orders":   {"key": "o_orderkey", "lower": 1, "upper": 15000000, "partitions": 100},
        "customer": {"key": "c_custkey",  "lower": 1, "upper": 1500000,  "partitions": 50},
        "part":     {"key": "p_partkey",  "lower": 1, "upper": 2000000,  "partitions": 50},
        "supplier": {"key": "s_suppkey",  "lower": 1, "upper": 100000,    "partitions": 10},
        "partsupp": {"key": "ps_partkey", "lower": 1, "upper": 8000000,   "partitions": 50},
        "nation":   {"key": "n_nationkey","lower": 0, "upper": 25,        "partitions": 1},
        "region":   {"key": "r_regionkey","lower": 0, "upper": 5,         "partitions": 1},
    }

    table_names = list(table_partition_config.keys())
    tables = {}

    for table in table_names:
        config = table_partition_config[table]
        if use_jdbc:
            if not all([jdbc_url, jdbc_user, jdbc_password]):
                raise ValueError(f"JDBC connection parameters missing for {table}")

            print(f"Loading {table} via JDBC with {config['partitions']} partitions...")
            df = spark.read.format("jdbc").options(
                url=jdbc_url,
                dbtable=table,
                user=jdbc_user,
                password=jdbc_password,
                driver=jdbc_driver,
                partitionColumn=config["key"],
                lowerBound=config["lower"],
                upperBound=config["upper"],
                numPartitions=config["partitions"],
                fetchsize=5000          # reasonable fetch size
            ).load()
        else:
            # Fallback to Parquet files (useful for testing)
            base_path = os.getenv("TPCH_PARQUET_PATH", "/path/to/tpch_parquet")
            file_path = f"{base_path}/{table}.parquet"
            if os.path.exists(file_path):
                print(f"Loading {table} from Parquet: {file_path}")
                df = spark.read.parquet(file_path)
            else:
                print(f"Table {table} not found at {file_path}, skipping...")
                continue

        tables[table] = df

    return spark, tables
