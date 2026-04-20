#!/bin/bash
# ==============================================================================
# BenchPress JMeter Benchmark Runner
# Based on DLoader paper: "Migration of Data from SQL to NoSQL Databases"
# Benchmarks MongoDB, Cassandra, and MySQL (baseline) with TPC-H data
# ==============================================================================

set -e

# --- Configuration ---
THREADS=${1:-5}           # Number of concurrent threads (default: 5)
LOOPS=${2:-100}           # Number of loops per thread (default: 100)
REPORT_DIR="jmeter_reports"
RESULTS_FILE="results.jtl"
JMX_FILE="benchmark_nosql.jmx"

# JMeter Home (adjust if different)
export JMETER_HOME=${JMETER_HOME:-/opt/homebrew/Cellar/jmeter/5.6.3}
export PATH=$JMETER_HOME/bin:$PATH

# --- Classpath: MongoDB + Cassandra + MySQL drivers ---
CLASSPATH=""
for jar in jmeter-libs/*.jar; do
    if [ -f "$jar" ]; then
        CLASSPATH="${CLASSPATH}${CLASSPATH:+:}$jar"
    fi
done

# Add MySQL connector
MYSQL_JAR="mysql-connector-j-8.0.33/mysql-connector-j-8.0.33.jar"
if [ -f "$MYSQL_JAR" ]; then
    CLASSPATH="${CLASSPATH}:${MYSQL_JAR}"
fi

echo "============================================================"
echo "  BenchPress - DLoader NoSQL Benchmark (TPC-H)"
echo "============================================================"
echo ""
echo "  Threads:    ${THREADS}"
echo "  Loops:      ${LOOPS}"
echo "  JMX File:   ${JMX_FILE}"
echo "  Results:    ${RESULTS_FILE}"
echo "  Reports:    ${REPORT_DIR}/index.html"
echo ""
echo "  Queries per database:"
echo "    Q1: Point query (read customer by ID)"
echo "    Q2: Detail query (customer orders + lineitems)"
echo "    Q3: Aggregation (count orders by status)"
echo "    Q4: Range query (customers by region)"
echo "    Q5: Revenue aggregation (analytical)"
echo ""
echo "  Databases:  MongoDB | Cassandra | MySQL (baseline)"
echo "============================================================"
echo ""

# Clean previous results
rm -rf "$RESULTS_FILE" "$REPORT_DIR"
mkdir -p "$REPORT_DIR"

echo "[$(date '+%H:%M:%S')] Starting JMeter benchmark..."
echo ""

jmeter -n \
    -t "$JMX_FILE" \
    -l "$RESULTS_FILE" \
    -e -o "$REPORT_DIR" \
    -JTHREADS="$THREADS" \
    -JLOOPS="$LOOPS" \
    -Juser.classpath="$CLASSPATH"

echo ""
echo "============================================================"
echo "  Benchmark complete!"
echo "============================================================"
echo ""
echo "  Results:     ${RESULTS_FILE}"
echo "  HTML Report: ${REPORT_DIR}/index.html"
echo ""
echo "  Open report: open ${REPORT_DIR}/index.html"
echo "============================================================"
