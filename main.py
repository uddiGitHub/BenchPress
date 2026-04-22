from extract import extract_tpch_tables
from stagging import stage_to_local
from transform import transform_data
from mapping import map_to_Mongos, map_to_cassandra, apply_partitioning
from load import load_parquet_to_mongodb,convert_doc,create_cassandra_keyspace_and_table, load_to_cassandra
import os

def main():
    spark, tables = extract_tpch_tables()

    stage_to_local(tables)

    denorm_df = transform_data(spark)

    # MongoDB path: nested documents
    doc_df_mongos = map_to_Mongos(denorm_df)
    doc_df_mongos = apply_partitioning(doc_df_mongos)

    doc_df_mongos = convert_doc(doc_df_mongos)

    temp_parquet_path = "data/final_customersMongos.parquet"
    doc_df_mongos.write.mode("overwrite").parquet(temp_parquet_path)
    load_parquet_to_mongodb(temp_parquet_path, collection_name="customers")

    # Cassandra path: flat denormalized data
    doc_df_cassandra, cassandra_table = map_to_cassandra(denorm_df)
    doc_df_cassandra = apply_partitioning(doc_df_cassandra)


    # Ensure Cassandra keyspace and table exist
    create_cassandra_keyspace_and_table()

    # Write to Cassandra (overwrite mode to avoid duplicates)
    load_to_cassandra(doc_df_cassandra, table_name=cassandra_table, truncate_first=True)

    print("✅ Migration to MongoDB and Cassandra completed successfully.")
    spark.stop()

if __name__ == "__main__":
    main()