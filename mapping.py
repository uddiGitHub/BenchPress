from pyspark.sql.functions import collect_list, struct, col, first

def map_to_nosql(df):
    # First, nest lineitems inside orders, while keeping all customer fields
    orders_nested = df.groupBy(
        "customer_id", "order_id", "name", "nation_name", "region_name"
    ).agg(
        first("status").alias("status"),
        first("total_price").alias("total_price"),
        first("order_date").alias("order_date"),
        collect_list(
            struct(
                col("line_number"),
                col("quantity"),
                col("extended_price"),
                col("discount"),
                col("tax"),
                col("return_flag"),
                col("line_status"),
                col("ship_date"),
                col("commit_date"),
                col("receipt_date")
            )
        ).alias("lineitems")
    )

    # Then nest orders under customer, using the preserved fields
    customer_docs = orders_nested.groupBy("customer_id").agg(
        first("name").alias("name"),
        first("nation_name").alias("nation"),
        first("region_name").alias("region"),
        collect_list(
            struct(
                col("order_id"),
                col("status"),
                col("total_price"),
                col("order_date"),
                col("lineitems")
            )
        ).alias("orders")
    )

    return customer_docs

def apply_partitioning(df):
    """Repartition by customer_id for balanced parallel writes."""
    return df.repartition(8, "customer_id")  