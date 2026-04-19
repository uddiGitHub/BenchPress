import os
import pymongo
import pyarrow.parquet as pq
import numpy as np
from decimal import Decimal
import datetime
from bson.decimal128 import Decimal128
from pymongo.errors import DocumentTooLarge, BulkWriteError
from cassandra.cluster import Cluster
from dotenv import load_dotenv

load_dotenv()

def convert_doc(doc):
    """Recursively convert Decimal -> Decimal128, date -> datetime, NumPy -> Python types."""
    if isinstance(doc, dict):
        return {k: convert_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [convert_doc(item) for item in doc]
    elif isinstance(doc, np.ndarray):
        return convert_doc(doc.tolist())
    elif isinstance(doc, (np.integer, np.int64, np.int32)):
        return int(doc)
    elif isinstance(doc, (np.floating, np.float64, np.float32)):
        return float(doc)
    elif isinstance(doc, Decimal):
        # Use Decimal128 for exact monetary values
        return Decimal128(str(doc))
    elif isinstance(doc, datetime.date):
        return datetime.datetime(doc.year, doc.month, doc.day)
    else:
        return doc

def load_parquet_to_mongodb(parquet_path, collection_name, batch_size=5000):
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI not set in .env file")
    db_name = os.getenv("MONGODB_DATABASE", "tpch10gb")

    client = pymongo.MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]
    collection.drop()   # overwrite mode

    table = pq.read_table(parquet_path)
    num_rows = table.num_rows
    print(f"Loaded {num_rows} rows from {parquet_path}")

    inserted_total = 0
    for start in range(0, num_rows, batch_size):
        end = min(start + batch_size, num_rows)
        batch = table.slice(start, end - start)
        df_batch = batch.to_pandas()
        records = df_batch.to_dict(orient="records")
        if not records:
            continue

        converted_records = [convert_doc(rec) for rec in records]

        try:
            collection.insert_many(converted_records, ordered=False)
            inserted_total += len(converted_records)
            print(f"Inserted {end} of {num_rows} documents...")
        except (DocumentTooLarge, BulkWriteError) as e:
            print(f"Batch failed: {e}. Falling back to one‑by‑one insertion.")
            # Retry one by one to skip oversize documents
            for rec in converted_records:
                try:
                    collection.insert_one(rec)
                    inserted_total += 1
                except DocumentTooLarge:
                    customer_id = rec.get("customer_id", "unknown")
                    print(f"Skipping customer {customer_id} – document exceeds 16MB")
                except Exception as inner_e:
                    print(f"Failed to insert document: {inner_e}")

    print(f"✅ Loaded {inserted_total} documents into {db_name}.{collection_name}")
    client.close()

def create_cassandra_keyspace_and_table():
    """
    Create keyspace and table in Cassandra using the native driver.
    """
    hosts = [os.getenv("CASSANDRA_HOST", "localhost")]
    port = int(os.getenv("CASSANDRA_PORT", "9042"))
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "tpch1gb")

    cluster = Cluster(hosts, port=port)
    session = cluster.connect()

    # Create keyspace if not exists
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH REPLICATION = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)

    # Use the keyspace
    session.set_keyspace(keyspace)

    # Create table if not exists (matches schema used in map_to_cassandra)
    session.execute("""
        CREATE TABLE IF NOT EXISTS customer_orders (
            customer_id INT,
            order_id INT,
            line_number INT,
            name TEXT,
            nation TEXT,
            region TEXT,
            status TEXT,
            total_price DECIMAL,
            order_date DATE,
            quantity DECIMAL,
            extended_price DECIMAL,
            discount DECIMAL,
            tax DECIMAL,
            return_flag TEXT,
            line_status TEXT,
            ship_date DATE,
            commit_date DATE,
            receipt_date DATE,
            PRIMARY KEY ((customer_id), order_id, line_number)
        )
    """)
    cluster.shutdown()
    print(f"Cassandra keyspace '{keyspace}' and table 'customer_orders' ready.")


def load_to_cassandra(df, table_name="customer_orders", truncate_first=False):
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "tpch1gb")
    
    if truncate_first:
        # Truncate the table using Cassandra driver
        from cassandra.cluster import Cluster
        cluster = Cluster([os.getenv("CASSANDRA_HOST", "localhost")], port=int(os.getenv("CASSANDRA_PORT", "9042")))
        session = cluster.connect(keyspace)
        session.execute(f"TRUNCATE {table_name}")
        cluster.shutdown()
        print(f"Truncated {keyspace}.{table_name}")
    
    df.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(
            keyspace=keyspace,
            table=table_name
        ) \
        .mode("append") \
        .save()
    print(f"✅ Loaded data into Cassandra table {keyspace}.{table_name}.")