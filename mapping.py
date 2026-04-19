import os
from pyspark.sql.functions import collect_list, struct, col, first
from pyspark.sql.types import DecimalType

def map_to_Mongos(df):
    """Nest orders and lineitems into a per‑customer document."""
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


def map_to_cassandra(df, table_name="customer_orders"):
    """Return flat DataFrame for Cassandra."""
    from pyspark.sql.types import DecimalType
    cassandra_df = df.select(
        df["customer_id"].cast("int"),
        df["order_id"].cast("int"),
        df["name"],
        df["nation_name"].alias("nation"),
        df["region_name"].alias("region"),
        df["status"],
        df["total_price"].cast(DecimalType(15,2)),
        df["order_date"].cast("date"),
        df["line_number"].cast("int"),
        df["quantity"].cast(DecimalType(15,2)),
        df["extended_price"].cast(DecimalType(15,2)),
        df["discount"].cast(DecimalType(15,2)),
        df["tax"].cast(DecimalType(15,2)),
        df["return_flag"],
        df["line_status"],
        df["ship_date"].cast("date"),
        df["commit_date"].cast("date"),
        df["receipt_date"].cast("date"),
    ).dropna(subset=["customer_id", "order_id", "line_number"])
    return cassandra_df, table_name

def apply_partitioning(df):
    return df.repartition(8, "customer_id")