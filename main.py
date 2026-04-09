from extract import extract_tpch_tables
from stagging import stage_to_hdfs
from transform import transform_data
from mapping import map_to_nosql, apply_partitioning
from load import load_to_mongodb

def main():
    # Step 1: Extract
    spark, tables = extract_tpch_tables()

    # Step 2: Stage all tables to HDFS / local Parquet
    stage_to_hdfs(tables)

    # Step 3: Transform (joins + enrichment)
    denorm_df = transform_data(spark)

    # Step 4: Map to nested document structure
    doc_df = map_to_nosql(denorm_df)

    # Step 5: Partition for efficient MongoDB writes
    doc_df = apply_partitioning(doc_df)

    # Step 6: Load to MongoDB
    load_to_mongodb(doc_df, collection_name="customers")

    print("TPC-H Migration to MongoDB Completed Successfully")
    spark.stop()

if __name__ == "__main__":
    main()