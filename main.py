import os
import sys
import argparse

# ─── Force unbuffered stdout under spark-submit ──────────────────────────────
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from extract import extract_tpch_tables
from stagging import stage_to_local
from transform import transform_data
from mapping import map_to_Mongos, map_to_cassandra, apply_partitioning
from load import load_parquet_to_mongodb, convert_doc, create_cassandra_keyspace_and_table, load_to_cassandra

# ─── ANSI Colors ─────────────────────────────────────────────────────────────
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
RESET  = "\033[0m"

def print_header(title):
    """Print a styled stage header."""
    width = 60
    print(f"\n{CYAN}{'━' * width}", flush=True)
    print(f"  {BOLD}{title}{RESET}{CYAN}", flush=True)
    print(f"{'━' * width}{RESET}\n", flush=True)

def print_status(message):
    """Print a status message."""
    print(f"  {GREEN}✔{RESET} {message}", flush=True)

def print_warn(message):
    """Print a warning/info message."""
    print(f"  {YELLOW}⚠{RESET} {message}", flush=True)

def parse_args():
    """
    Parse command-line arguments to control which pipeline stages to run.

    NOTE: spark-submit does not allow interactive stdin (input() hangs),
    so we use CLI flags instead. Pass flags to select stages:

        spark-submit ... main.py --stages extract stage transform mongodb cassandra
        spark-submit ... main.py --stages extract stage transform mongodb
        spark-submit ... main.py --all           # run everything (default)
        spark-submit ... main.py --skip mongodb   # run all except MongoDB
    """
    parser = argparse.ArgumentParser(
        description="BenchPress — SQL → NoSQL Migration Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run full pipeline (default):
    spark-submit ... main.py
    spark-submit ... main.py --all

  Run only specific stages:
    spark-submit ... main.py --stages extract stage transform mongodb
    spark-submit ... main.py --stages extract stage transform cassandra

  Skip specific stages:
    spark-submit ... main.py --skip mongodb
    spark-submit ... main.py --skip cassandra
    spark-submit ... main.py --skip mongodb cassandra
        """
    )

    parser.add_argument(
        "--stages", nargs="+",
        choices=["extract", "stage", "transform", "mongodb", "cassandra"],
        help="Run only these stages (order is fixed internally)"
    )
    parser.add_argument(
        "--skip", nargs="+",
        choices=["extract", "stage", "transform", "mongodb", "cassandra"],
        help="Skip these stages (run everything else)"
    )
    parser.add_argument(
        "--all", action="store_true", default=True,
        help="Run all stages (default behavior)"
    )

    args = parser.parse_args()

    all_stages = ["extract", "stage", "transform", "mongodb", "cassandra"]

    if args.stages:
        return set(args.stages)
    elif args.skip:
        return set(all_stages) - set(args.skip)
    else:
        return set(all_stages)


def main():
    active_stages = parse_args()

    print_header("BENCHPRESS — SQL → NoSQL MIGRATION PIPELINE")
    print(f"  Active stages:", flush=True)
    stage_labels = {
        "extract":   "Extract  — Load TPC-H tables from source",
        "stage":     "Stage    — Write raw tables to local Parquet",
        "transform": "Transform — Denormalize & enrich data",
        "mongodb":   "Load to MongoDB",
        "cassandra": "Load to Cassandra",
    }
    for key, label in stage_labels.items():
        marker = f"{GREEN}●{RESET}" if key in active_stages else f"{RED}○{RESET}"
        print(f"    {marker} {label}", flush=True)
    print(flush=True)

    # ── 1. EXTRACT ────────────────────────────────────────────────────────────
    if "extract" in active_stages:
        print_header("STAGE 1 — EXTRACTION")
        print(f"  {YELLOW}⏳ Initializing Spark & loading tables (this may take a minute)...{RESET}", flush=True)
        spark, tables = extract_tpch_tables()
        print_status(f"Extracted {len(tables)} tables: {', '.join(tables.keys())}")
    else:
        print_warn("Skipping extraction — this requires pre-existing Spark session")
        sys.exit(1)

    # ── 2. STAGE ──────────────────────────────────────────────────────────────
    if "stage" in active_stages:
        print_header("STAGE 2 — STAGING")
        print(f"  {YELLOW}⏳ Writing tables to Parquet...{RESET}", flush=True)
        stage_to_local(tables)
        print_status("All tables staged to data/staging/")
    else:
        print_warn("Skipping staging")

    # ── 3. TRANSFORM ──────────────────────────────────────────────────────────
    if "transform" in active_stages:
        print_header("STAGE 3 — TRANSFORMATION & MAPPING")
        print(f"  {YELLOW}⏳ Denormalizing & enriching data (joins in progress)...{RESET}", flush=True)
        denorm_df = transform_data(spark)
        print_status("Denormalized dataset ready")
    else:
        print_warn("Skipping transform — loading stages require this")
        if "mongodb" in active_stages or "cassandra" in active_stages:
            print(f"  {RED}✖ Cannot load to databases without transform. Aborting.{RESET}", flush=True)
            spark.stop()
            sys.exit(1)

    # ── 4. LOAD TO MONGODB ────────────────────────────────────────────────────
    if "mongodb" in active_stages:
        print_header("STAGE 4 — MONGODB LOAD")
        print(f"  {YELLOW}⏳ Mapping to MongoDB document structure...{RESET}", flush=True)
        doc_df_mongos = map_to_Mongos(denorm_df)
        doc_df_mongos = apply_partitioning(doc_df_mongos)
        doc_df_mongos = convert_doc(doc_df_mongos)

        temp_parquet_path = "data/final_customersMongos.parquet"
        doc_df_mongos.write.mode("overwrite").parquet(temp_parquet_path)
        print(f"  {YELLOW}⏳ Inserting documents into MongoDB...{RESET}", flush=True)
        load_parquet_to_mongodb(temp_parquet_path, collection_name="customers")
        print_status("MongoDB load complete")
    else:
        print_warn("Skipping MongoDB load")

    # ── 5. LOAD TO CASSANDRA ──────────────────────────────────────────────────
    if "cassandra" in active_stages:
        print_header("STAGE 5 — CASSANDRA LOAD")
        print(f"  {YELLOW}⏳ Mapping to Cassandra table structure...{RESET}", flush=True)
        doc_df_cassandra, cassandra_table = map_to_cassandra(denorm_df)
        doc_df_cassandra = apply_partitioning(doc_df_cassandra)
        create_cassandra_keyspace_and_table()
        print(f"  {YELLOW}⏳ Writing data to Cassandra...{RESET}", flush=True)
        load_to_cassandra(doc_df_cassandra, table_name=cassandra_table, truncate_first=True)
        print_status("Cassandra load complete")
    else:
        print_warn("Skipping Cassandra load")

    # ── DONE ──────────────────────────────────────────────────────────────────
    print_header("PIPELINE COMPLETED SUCCESSFULLY")
    spark.stop()


if __name__ == "__main__":
    main()