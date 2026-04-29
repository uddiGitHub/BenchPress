import os
from pyspark.sql.functions import collect_list, struct, col, first
from pyspark.sql.types import DecimalType

# ─── ANSI Colors ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def _log(msg):
    print(f"  {msg}", flush=True)

def map_to_Mongos(df):
    """Nest orders and lineitems into a per‑customer document."""
    _log(f"{YELLOW}⏳ Nesting lineitems into orders (groupBy order_id)...{RESET}")

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
    _log(f"{GREEN}✔{RESET} Orders nested with lineitems array")

    _log(f"{YELLOW}⏳ Nesting orders into customer documents (groupBy customer_id)...{RESET}")
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
    _log(f"{GREEN}✔{RESET} MongoDB document structure ready")
    _log(f"{DIM}  Schema: customer_id, name, nation, region, orders[order_id, status, total_price, order_date, lineitems[...]]{RESET}")
    return customer_docs


def map_to_cassandra(df, table_name="customer_orders"):
    """Return flat DataFrame for Cassandra."""
    _log(f"{YELLOW}⏳ Flattening for Cassandra table '{table_name}'...{RESET}")

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

    col_count = len(cassandra_df.columns)
    _log(f"{GREEN}✔{RESET} Cassandra flat table ready — {CYAN}{col_count} columns{RESET}")
    _log(f"{DIM}  PK: (customer_id), order_id, line_number{RESET}")
    return cassandra_df, table_name


def apply_partitioning(df):
    _log(f"{YELLOW}⏳ Repartitioning to 8 partitions on customer_id...{RESET}")
    repartitioned = df.repartition(8, "customer_id")
    _log(f"{GREEN}✔{RESET} Repartitioned to {CYAN}8{RESET} partitions")
    return repartitioned