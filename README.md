# BenchPress

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PySpark](https://img.shields.io/badge/PySpark-3.5.0-orange.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-supported-green.svg)
![Cassandra](https://img.shields.io/badge/Cassandra-supported-purple.svg)
![MySQL](https://img.shields.io/badge/MySQL-optional-lightgrey.svg)

BenchPress is a local ETL/data migration pipeline built with **PySpark** for moving **TPC-H style relational data** into two downstream stores:

- **MongoDB** as nested customer documents
- **Cassandra** as flat denormalized rows

The pipeline reads normalized source data either from **MySQL via JDBC** or from **Parquet files**, stages the data locally, denormalizes it with Spark, then writes transformed outputs to MongoDB and Cassandra.

---

## Overview

The project is organized as a simple end-to-end pipeline:

1. **Extract** source TPC-H tables from MySQL or Parquet
2. **Stage** them as local Parquet files under `data/staging/`
3. **Transform** and denormalize customer, order, and line item data
4. **Map** the transformed data into:
   - nested MongoDB documents
   - flat Cassandra rows
5. **Load** the results into MongoDB and Cassandra

The full flow is orchestrated from `main.py`.

---

## Pipeline Flow

### 1. Extraction — `extract.py`
Creates a Spark session and loads TPC-H tables:

- `customer`
- `orders`
- `lineitem`
- `nation`
- `region`
- `part`
- `supplier`
- `partsupp`

Source options:

- **JDBC** from MySQL when `TPCH_USE_JDBC=true`
- **Parquet files** when `TPCH_USE_JDBC=false`

Notable behavior:

- Configures Spark packages for:
  - MongoDB Spark Connector
  - Spark Cassandra Connector
  - MySQL JDBC Driver
- Tunes partitioned JDBC reads for larger tables such as `lineitem`, `orders`, and `customer`
- Reads Parquet from `TPCH_PARQUET_PATH` when not using JDBC

### 2. Staging — `stagging.py`
Writes extracted tables to local Parquet:

- Default path: `data/staging/`

This gives the pipeline a checkpoint between extraction and transformation.

### 3. Transformation — `transform.py`
Reads staged Parquet files and denormalizes the dataset by joining:

- `customer`
- `orders`
- `lineitem`
- `nation`
- `region`

Transform details:

- Renames source columns into more usable business fields
- Joins orders to line items
- Joins customers to orders
- Enriches results with nation and region metadata

### 4. Mapping — `mapping.py`
Builds two target representations from the denormalized DataFrame:

#### MongoDB mapping
`map_to_Mongos(df)` creates nested customer documents shaped like:

- customer
  - orders[]
    - lineitems[]

#### Cassandra mapping
`map_to_cassandra(df)` creates a flat denormalized table-ready DataFrame for Cassandra.

Also includes:

- `apply_partitioning(df)` → repartitions by `customer_id`

### 5. Loading — `load.py`

#### MongoDB load
- Reads intermediate Parquet output with `pyarrow`
- Converts Python/NumPy/Decimal/date values into MongoDB-compatible values
- Drops the destination collection before loading
- Inserts documents in batches
- Falls back to one-by-one inserts when a batch fails
- Skips oversized MongoDB documents when necessary

#### Cassandra load
- Creates the keyspace if it does not exist
- Creates the `customer_orders` table if it does not exist
- Optionally truncates the table before loading
- Writes data using the Spark Cassandra connector

---

## Actual Runtime Flow

`main.py` runs the following sequence:

1. `extract_tpch_tables()`
2. `stage_to_local(tables)`
3. `transform_data(spark)`
4. MongoDB branch:
   - `map_to_Mongos(...)`
   - `apply_partitioning(...)`
   - write temporary Parquet to `data/final_customersMongos.parquet`
   - `load_parquet_to_mongodb(...)`
5. Cassandra branch:
   - `map_to_cassandra(...)`
   - `apply_partitioning(...)`
   - `create_cassandra_keyspace_and_table()`
   - `load_to_cassandra(...)`

Successful completion prints:

```text
✅ Migration to MongoDB and Cassandra completed successfully.
```

---

## Project Structure

```bash
BenchPress/
├── .env
├── README.md
├── requirements.txt
├── main.py                          # ETL pipeline orchestrator
├── extract.py                       # TPC-H data extraction (MySQL/Parquet)
├── stagging.py                      # Stage data as local Parquet
├── transform.py                     # Denormalize and join tables
├── mapping.py                       # Map to MongoDB/Cassandra schemas
├── load.py                          # Load into MongoDB and Cassandra
├── benchmark_nosql.jmx              # JMeter test plan (15 queries)
├── run_jmeter_tests.sh              # Benchmark runner script
├── scripts/                         # External Groovy scripts for JMeter
│   ├── mongo_q1.groovy              # MongoDB Q1: Point query
│   ├── mongo_q2.groovy              # MongoDB Q2: Orders detail (aggregation)
│   ├── mongo_q3.groovy              # MongoDB Q3: Orders by status
│   ├── mongo_q4.groovy              # MongoDB Q4: Range query by region
│   ├── mongo_q5.groovy              # MongoDB Q5: Revenue aggregation
│   ├── cassandra_q1.groovy          # Cassandra Q1: Partition key lookup
│   ├── cassandra_q2.groovy          # Cassandra Q2: Full partition scan
│   ├── cassandra_q3.groovy          # Cassandra Q3: Distinct order count
│   ├── cassandra_q4.groovy          # Cassandra Q4: Filter by return flag
│   ├── cassandra_q5.groovy          # Cassandra Q5: Revenue aggregation
│   ├── mysql_q1.groovy              # MySQL Q1: JOIN point query
│   ├── mysql_q2.groovy              # MySQL Q2: Multi-table JOIN
│   ├── mysql_q3.groovy              # MySQL Q3: GROUP BY aggregation
│   ├── mysql_q4.groovy              # MySQL Q4: Range with JOIN
│   ├── mysql_q5.groovy              # MySQL Q5: Revenue SUM
│   └── teardown.groovy              # Close all DB connections
├── jmeter-libs/                     # MongoDB & Cassandra Java driver JARs
├── mysql-connector-j-8.0.33/        # MySQL JDBC connector
├── data/
│   ├── staging/                     # Generated staged Parquet data
│   └── final_customersMongos.parquet # Generated intermediate MongoDB output
├── results.jtl                      # Generated JMeter raw results
├── jmeter_reports/                  # Generated HTML benchmark reports
└── Data Migration SQL to NoSQL.pdf  # Reference paper
```

---

## Requirements

Install the following locally:

- **Python 3.9+**
- **Java** compatible with your Spark/PySpark setup
- **MongoDB**
- **Cassandra**
- **MySQL** only if using JDBC extraction

Python dependencies are listed in `requirements.txt`:

- `pyspark==3.5.0`
- `python-dotenv==1.2.1`
- `pymongo==4.6.1`
- `pyarrow==15.0.0`
- `pandas==2.3.3`
- `cassandra-driver==3.29.3`

---

## Installation

Create and activate a virtual environment, then install dependencies.

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the project root.

### Option A: Read from MySQL via JDBC

```properties
TPCH_USE_JDBC=true
TPCH_JDBC_URL=jdbc:mysql://localhost:3306/tpch
TPCH_JDBC_USER=root
TPCH_JDBC_PASSWORD=your_password
TPCH_JDBC_DRIVER=com.mysql.cj.jdbc.Driver

MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=tpch10gb

CASSANDRA_HOST=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=tpch1gb
```

### Option B: Read from Parquet files

```properties
TPCH_USE_JDBC=false
TPCH_PARQUET_PATH=/absolute/path/to/tpch_parquet

MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=tpch10gb

CASSANDRA_HOST=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=tpch1gb
```

### Important environment variables actually used by the code

| Variable | Purpose |
|---|---|
| `TPCH_USE_JDBC` | Switch between JDBC and Parquet input |
| `TPCH_JDBC_URL` | MySQL JDBC connection URL |
| `TPCH_JDBC_USER` | MySQL username |
| `TPCH_JDBC_PASSWORD` | MySQL password |
| `TPCH_JDBC_DRIVER` | JDBC driver class, defaults to `com.mysql.cj.jdbc.Driver` |
| `TPCH_PARQUET_PATH` | Base directory containing source Parquet tables |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DATABASE` | MongoDB database name, defaults to `tpch10gb` |
| `CASSANDRA_HOST` | Cassandra host, defaults to `localhost` |
| `CASSANDRA_PORT` | Cassandra port, defaults to `9042` |
| `CASSANDRA_KEYSPACE` | Cassandra keyspace, defaults to `tpch1gb` |

---

## Running the Pipeline

Run the pipeline from the project root:

```bash
spark-submit --packages com.datastax.spark:spark-cassandra-connector_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.3.0,com.mysql:mysql-connector-j:8.0.33,com.github.jnr:jnr-posix:3.1.15 --driver-memory 6g --executor-memory 6g main.py
```
---

## Output Targets

### MongoDB
The MongoDB loader writes to:

- database: `MONGODB_DATABASE` or `tpch1gb`
- collection: `customers`

The collection is dropped before each load.

### Cassandra
The Cassandra loader creates and writes to:

- keyspace: `CASSANDRA_KEYSPACE` or `tpch1gb`
- table: `customer_orders`

Primary key:

```sql
PRIMARY KEY ((customer_id), order_id, line_number)
```

---

## Example MongoDB Document Shape

A MongoDB customer document is structured approximately like this:

```json
{
  "customer_id": 1,
  "name": "Customer#000000001",
  "nation": "ALGERIA",
  "region": "AFRICA",
  "orders": [
    {
      "order_id": 123,
      "status": "O",
      "total_price": 12345.67,
      "order_date": "1996-01-02",
      "lineitems": [
        {
          "line_number": 1,
          "quantity": 17.0,
          "extended_price": 21168.23,
          "discount": 0.04,
          "tax": 0.02,
          "return_flag": "N",
          "line_status": "O",
          "ship_date": "1996-03-13",
          "commit_date": "1996-02-12",
          "receipt_date": "1996-03-22"
        }
      ]
    }
  ]
}
```

---

## JMeter Benchmarking

Based on the **DLoader paper** ("Migration of Data from SQL to NoSQL Databases" by K. Rajaram et al.), a comprehensive JMeter benchmark suite compares read performance across MongoDB, Cassandra, and MySQL.

### Benchmark Queries

The paper defines two core queries adapted to the TPC-H dataset, plus three extended analytical queries:

| Query | Description | MongoDB | Cassandra | MySQL |
|---|---|---|---|---|
| **Q1** | Point query: read customer by ID | `find({customer_id: X})` | `SELECT ... WHERE customer_id = X LIMIT 1` | `SELECT ... JOIN nation JOIN region WHERE c_custkey = ?` |
| **Q2** | Detail query: all orders + lineitems | Aggregation pipeline with `$unwind` | `SELECT * WHERE customer_id = X` | 4-table JOIN (customer→orders→lineitem) |
| **Q3** | Aggregation: count orders by status | `$group` by order status | Client-side distinct count | `GROUP BY o_orderstatus` |
| **Q4** | Range/filter query | Range on customer_id + region filter | Partition scan + return_flag filter | `BETWEEN` with region JOIN |
| **Q5** | Revenue aggregation | `$multiply` / `$subtract` pipeline | Client-side revenue computation | `SUM(price * (1-discount) * (1+tax))` |

### Running the Benchmark

```bash
# Default: 5 threads, 100 loops per thread
./run_jmeter_tests.sh

# Custom: 10 threads, 200 loops
./run_jmeter_tests.sh 10 200

# View the HTML report
open jmeter_reports/index.html
```

### Results (5 threads × 100 loops)

| Query | MongoDB Avg (ms) | Cassandra Avg (ms) | MySQL Avg (ms) |
|---|---|---|---|
| Q1 - Point Query | 43 | 3 | 11 |
| Q2 - Detail Query | 76 | 2 | 20 |
| Q3 - Aggregation | 72 | 1 | 13 |
| Q4 - Range/Filter | 78 | 2 | 12 |
| Q5 - Revenue | 82 | 3 | 43 |

Cassandra offers the best read performance across all query types, consistent with the paper's findings.

### Benchmark Configuration

The JMX test plan uses configurable variables:

| Variable | Default | Description |
|---|---|---|
| `THREADS` | 5 | Number of concurrent threads |
| `LOOPS` | 100 | Number of iterations per thread |
| `MAX_CUSTOMER_ID` | 150000 | Upper bound for random customer ID generation |
| `MONGO_HOST` | localhost | MongoDB host |
| `CASSANDRA_HOST` | localhost | Cassandra host |
| `MYSQL_HOST` | localhost | MySQL host |

Thread groups run sequentially (MongoDB → Cassandra → MySQL) to avoid cross-database interference. All database connections are reused across iterations and cleaned up in a teardown phase.

---

## Notes

- `stagging.py` is the current staging module filename used by the code.
- The current implementation writes a temporary Parquet file before loading MongoDB:
  - `data/final_customersMongos.parquet`
- The MongoDB load path uses `pyarrow + pymongo`, not Spark direct write.
- The Cassandra load path uses both:
  - native Python Cassandra driver for schema management/truncation
  - Spark Cassandra connector for bulk writes
- JMeter benchmark scripts are kept as external `.groovy` files in `scripts/` to avoid XML encoding issues with inline Groovy in JMX files.

---

## Limitations / Things to Know

- The pipeline assumes TPC-H style table names and schemas.
- Partition bounds in `extract.py` are hardcoded for expected TPC-H ranges.
- MongoDB documents that exceed the 16 MB BSON size limit are skipped during fallback insertion.
- Cassandra replication is currently set to `SimpleStrategy` with replication factor `1`.
- The pipeline is designed for local execution and experimentation, not yet production orchestration.

---

## Repository Purpose

This repo demonstrates how to migrate and remodel normalized analytical data into multiple NoSQL-friendly target shapes using Spark:

- **document-oriented** for MongoDB
- **wide-column / flat denormalized** for Cassandra

It is useful for benchmarking, experimentation, and learning ETL/data modeling patterns across SQL and NoSQL systems.

