import sys

# ─── ANSI Colors ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def _log(msg):
    print(f"  {msg}", flush=True)

def transform_data(spark, staging_path="data/staging"):
    _log(f"{YELLOW}⏳ Reading staging tables...{RESET}")

    # Read all necessary tables from staging
    customer = spark.read.parquet(f"{staging_path}/customer")
    orders = spark.read.parquet(f"{staging_path}/orders")
    lineitem = spark.read.parquet(f"{staging_path}/lineitem")
    nation = spark.read.parquet(f"{staging_path}/nation")
    region = spark.read.parquet(f"{staging_path}/region")

    _log(f"{GREEN}✔{RESET} Tables loaded: customer, orders, lineitem, nation, region")

    # Clean and rename for clarity
    _log(f"{YELLOW}⏳ Cleaning & renaming columns...{RESET}")
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

    _log(f"{GREEN}✔{RESET} Columns cleaned & renamed")

    # Join orders with lineitems
    _log(f"{YELLOW}⏳ Joining orders ⟶ lineitems (left join on order_id)...{RESET}")
    orders_with_items = orders.join(lineitem, "order_id", "left")
    _log(f"{GREEN}✔{RESET} Orders + lineitems joined")

    # Join customer with orders
    _log(f"{YELLOW}⏳ Joining customers ⟶ orders (left join on customer_id)...{RESET}")
    customer_orders = customer.join(orders_with_items, "customer_id", "left")
    _log(f"{GREEN}✔{RESET} Customers + orders joined")

    # Join with nation and region for dimensional enrichment
    _log(f"{YELLOW}⏳ Enriching with nation & region dimensions...{RESET}")
    nation = nation.withColumnRenamed("n_nationkey", "nation_key") \
                   .withColumnRenamed("n_name", "nation_name") \
                   .withColumnRenamed("n_regionkey", "region_key")
    region = region.withColumnRenamed("r_regionkey", "region_key") \
                   .withColumnRenamed("r_name", "region_name")

    with_nation = customer_orders.join(nation, "nation_key", "left")
    enriched = with_nation.join(region, "region_key", "left")

    col_count = len(enriched.columns)
    _log(f"{GREEN}✔{RESET} Enriched dataset ready — {CYAN}{col_count} columns{RESET}")
    _log(f"{DIM}  Columns: {', '.join(enriched.columns)}{RESET}")

    return enriched