def stage_to_hdfs(tables, staging_path="data/staging"):
    for name, df in tables.items():
        df.write.mode("overwrite").parquet(f"{staging_path}/{name}")