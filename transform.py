from pyspark.sql.functions import col

def transform_data(spark, staging_path="data/staging"):
    # Read all necessary tables from staging
    customer = spark.read.parquet(f"{staging_path}/customer")
    orders = spark.read.parquet(f"{staging_path}/orders")
    lineitem = spark.read.parquet(f"{staging_path}/lineitem")
    nation = spark.read.parquet(f"{staging_path}/nation")
    region = spark.read.parquet(f"{staging_path}/region")

    # Clean and rename for clarity
    customer = customer.dropna() \
        .withColumnRenamed("c_custkey", "customer_id") \
        .withColumnRenamed("c_name", "name") \
        .withColumnRenamed("c_nationkey", "nation_key")

    orders = orders.dropna() \
        .withColumnRenamed("o_orderkey", "order_id") \
        .withColumnRenamed("o_custkey", "customer_id") \
        .withColumnRenamed("o_orderstatus", "status") \
        .withColumnRenamed("o_totalprice", "total_price") \
        .withColumnRenamed("o_orderdate", "order_date")

    lineitem = lineitem.dropna() \
        .withColumnRenamed("l_orderkey", "order_id") \
        .withColumnRenamed("l_linenumber", "line_number") \
        .withColumnRenamed("l_quantity", "quantity") \
        .withColumnRenamed("l_extendedprice", "extended_price") \
        .withColumnRenamed("l_discount", "discount") \
        .withColumnRenamed("l_tax", "tax") \
        .withColumnRenamed("l_returnflag", "return_flag") \
        .withColumnRenamed("l_linestatus", "line_status") \
        .withColumnRenamed("l_shipdate", "ship_date") \
        .withColumnRenamed("l_commitdate", "commit_date") \
        .withColumnRenamed("l_receiptdate", "receipt_date") \
        .select("order_id", "line_number", "quantity", "extended_price",
                "discount", "tax", "return_flag", "line_status",
                "ship_date", "commit_date", "receipt_date")

    # Join orders with lineitems (left join to keep orders without items)
    orders_with_items = orders.join(lineitem, "order_id", "left")

    # Join customer with orders
    customer_orders = customer.join(orders_with_items, "customer_id", "left")

    # Join with nation and region for dimensional enrichment
    nation = nation.withColumnRenamed("n_nationkey", "nation_key") \
                   .withColumnRenamed("n_name", "nation_name") \
                   .withColumnRenamed("n_regionkey", "region_key")
    region = region.withColumnRenamed("r_regionkey", "region_key") \
                   .withColumnRenamed("r_name", "region_name")

    enriched = customer_orders.join(nation, "nation_key", "left") \
                              .join(region, "region_key", "left")

    return enriched