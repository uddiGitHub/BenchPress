#!/usr/bin/env python3
"""
BenchPress Report Generator
Generates a custom HTML comparison report from JMeter results.
Based on DLoader paper: "Migration of Data from SQL to NoSQL Databases"
"""

import csv
import os
import sys
import html as html_lib
from collections import defaultdict
from datetime import datetime

RESULTS_FILE = "results.jtl"
OUTPUT_FILE = "jmeter_reports/comparison_report.html"

# Query metadata for the comparison table
QUERY_MAP = [
    {
        "id": "Q1",
        "title": "Read customer by ID",
        "databases": [
            {
                "db": "Cassandra",
                "label": "Cassandra Q1 - Read Customer by ID",
                "operation": "Partition key row lookup on customer table",
                "script": "scripts/cassandra_q1.groovy",
                "differs": False,
                "code": "SELECT customer_id, name, nation, region \nFROM customer_orders \nWHERE customer_id = ? LIMIT 1;"
            },
            {
                "db": "MongoDB",
                "label": "MongoDB Q1 - Read Customer by ID",
                "operation": "Primary key document lookup on customer collection",
                "script": "scripts/mongo_q1.groovy",
                "differs": False,
                "code": "db.customers.find({ \n  customer_id: ? \n}).limit(1)"
            },
            {
                "db": "MySQL",
                "label": "MySQL Q1 - Read Customer by ID",
                "operation": "Indexed SELECT on customer table",
                "script": "scripts/mysql_q1.groovy",
                "differs": False,
                "code": "SELECT c.c_custkey, c.c_name, n.n_name AS nation, r.r_name AS region\nFROM customer c\nJOIN nation n ON c.c_nationkey = n.n_nationkey\nJOIN region r ON n.n_regionkey = r.r_regionkey\nWHERE c.c_custkey = ?;"
            },
        ],
    },
    {
        "id": "Q2",
        "title": "Read customer orders detail",
        "databases": [
            {
                "db": "Cassandra",
                "label": "Cassandra Q2 - Read Customer Orders Detail",
                "operation": "Partition key scan across orders table",
                "script": "scripts/cassandra_q2.groovy",
                "differs": False,
                "code": "SELECT * \nFROM customer_orders \nWHERE customer_id = ?;"
            },
            {
                "db": "MongoDB",
                "label": "MongoDB Q2 - Read Customer Orders Detail",
                "operation": "Embedded / linked orders sub-document lookup",
                "script": "scripts/mongo_q2.groovy",
                "differs": False,
                "code": "db.customers.aggregate([\n  { $match: { customer_id: ? } },\n  { $unwind: { path: '$orders', preserveNullAndEmptyArrays: true } },\n  { $unwind: { path: '$orders.lineitems', preserveNullAndEmptyArrays: true } },\n  { $project: { _id: 0, customer_id: 1, name: 1, 'orders.order_id': 1 /* ... */ } }\n])"
            },
            {
                "db": "MySQL",
                "label": "MySQL Q2 - Read Customer Orders Detail",
                "operation": "JOIN across customer & orders tables",
                "script": "scripts/mysql_q2.groovy",
                "differs": False,
                "code": "SELECT c.*, o.*, l.*\nFROM customer c\nJOIN orders o ON c.c_custkey = o.o_custkey\nJOIN lineitem l ON o.o_orderkey = l.l_orderkey\nWHERE c.c_custkey = ?;"
            },
        ],
    },
    {
        "id": "Q3",
        "title": "Aggregation: orders by status",
        "databases": [
            {
                "db": "Cassandra",
                "label": "Cassandra Q3 - Count Customer Orders",
                "operation": "COUNT per customer partition — no full aggregation support",
                "script": "scripts/cassandra_q3.groovy",
                "differs": True,
                "code": "// 1. Scan partition for order status\nSELECT order_id, line_number, status \nFROM customer_orders \nWHERE customer_id = ?;\n\n// 2. Client-side distinct count\nint count = 0;\nSet<Integer> uniqueOrders = new HashSet<>();\nfor (Row row : results) {\n  uniqueOrders.add(row.getInt(\"order_id\"));\n}\ncount = uniqueOrders.size();"
            },
            {
                "db": "MongoDB",
                "label": "MongoDB Q3 - Aggregation: Orders by Status",
                "operation": "Aggregation pipeline — group by order status",
                "script": "scripts/mongo_q3.groovy",
                "differs": False,
                "code": "db.customers.aggregate([\n  { $match: { customer_id: ? } },\n  { $unwind: '$orders' },\n  { $group: { \n      _id: '$orders.status', \n      order_count: { $sum: 1 },\n      total_value: { $sum: '$orders.total_price' }\n  }}\n])"
            },
            {
                "db": "MySQL",
                "label": "MySQL Q3 - Aggregation: Orders by Status",
                "operation": "GROUP BY on order status column",
                "script": "scripts/mysql_q3.groovy",
                "differs": False,
                "code": "SELECT o_orderstatus, COUNT(*) as order_count, SUM(o_totalprice)\nFROM orders\nWHERE o_custkey = ?\nGROUP BY o_orderstatus;"
            },
        ],
    },
    {
        "id": "Q4",
        "title": "Range / filter query",
        "databases": [
            {
                "db": "Cassandra",
                "label": "Cassandra Q4 - Filter by Return Flag",
                "operation": "Filtered scan on lineitems return flag — no cross-partition range",
                "script": "scripts/cassandra_q4.groovy",
                "differs": True,
                "code": "// Cannot do cross-partition range efficiently,\n// so we scan the customer's partition & filter.\nSELECT order_id, return_flag \nFROM customer_orders \nWHERE customer_id = ? \n  AND return_flag = 'R' ALLOW FILTERING;"
            },
            {
                "db": "MongoDB",
                "label": "MongoDB Q4 - Range Query: Customers by Region",
                "operation": "Range filter on nation / region field",
                "script": "scripts/mongo_q4.groovy",
                "differs": False,
                "code": "db.customers.find({\n  customer_id: { $gte: minId, $lte: maxId },\n  region: 'ASIA'\n})"
            },
            {
                "db": "MySQL",
                "label": "MySQL Q4 - Range Query: Customers by Region",
                "operation": "JOIN + WHERE clause filtering by region",
                "script": "scripts/mysql_q4.groovy",
                "differs": False,
                "code": "SELECT c.c_custkey, c.c_name \nFROM customer c\nJOIN nation n ON c.c_nationkey = n.n_nationkey\nJOIN region r ON n.n_regionkey = r.r_regionkey\nWHERE c.c_custkey BETWEEN ? AND ? \n  AND r.r_name = 'ASIA';"
            },
        ],
    },
    {
        "id": "Q5",
        "title": "Revenue aggregation",
        "databases": [
            {
                "db": "Cassandra",
                "label": "Cassandra Q5 - Revenue Aggregation",
                "operation": "SUM aggregation on lineitems partition",
                "script": "scripts/cassandra_q5.groovy",
                "differs": False,
                "code": "// 1. Scan partition for line items\nSELECT extended_price, discount \nFROM customer_orders \nWHERE customer_id = ?;\n\n// 2. Client-side revenue sum\ndouble revenue = 0;\nfor (Row row : results) {\n  revenue += row.extended_price * (1 - row.discount);\n}"
            },
            {
                "db": "MongoDB",
                "label": "MongoDB Q5 - Revenue Aggregation",
                "operation": "Pipeline SUM of extended price across lineitems",
                "script": "scripts/mongo_q5.groovy",
                "differs": False,
                "code": "db.customers.aggregate([\n  { $match: { customer_id: ? } },\n  { $unwind: '$orders' },\n  { $unwind: '$orders.lineitems' },\n  { $group: {\n      _id: null,\n      revenue: { \n        $sum: { \n          $multiply: [\n            '$orders.lineitems.extended_price', \n            { $subtract: [1, '$orders.lineitems.discount'] }\n          ]\n        }\n      }\n  }}\n])"
            },
            {
                "db": "MySQL",
                "label": "MySQL Q5 - Revenue Aggregation",
                "operation": "SUM with multi-table JOIN on TPC-H schema",
                "script": "scripts/mysql_q5.groovy",
                "differs": False,
                "code": "SELECT SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue\nFROM customer c\nJOIN orders o ON c.c_custkey = o.o_custkey\nJOIN lineitem l ON o.o_orderkey = l.l_orderkey\nWHERE c.c_custkey = ?;"
            },
        ],
    },
]

DB_COLORS = {
    "MongoDB": {"bg": "#e8f5e9", "badge": "#4caf50", "text": "#fff"},
    "Cassandra": {"bg": "#e3f2fd", "badge": "#1976d2", "text": "#fff"},
    "MySQL": {"bg": "#fff8e1", "badge": "#ff9800", "text": "#fff"},
}

DB_DOT_COLORS = {
    "MongoDB": "#4caf50",
    "Cassandra": "#1976d2",
    "MySQL": "#ff9800",
}


def parse_results(filepath):
    """Parse JMeter JTL CSV results file."""
    stats = defaultdict(lambda: {"count": 0, "total_time": 0, "min": float("inf"), "max": 0, "errors": 0})

    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Generating report without performance data.")
        return stats

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get("label", "")
            elapsed = int(row.get("elapsed", 0))
            success = row.get("success", "true")

            stats[label]["count"] += 1
            stats[label]["total_time"] += elapsed
            stats[label]["min"] = min(stats[label]["min"], elapsed)
            stats[label]["max"] = max(stats[label]["max"], elapsed)
            if success.lower() == "false":
                stats[label]["errors"] += 1

    # Compute averages
    for label in stats:
        s = stats[label]
        s["avg"] = round(s["total_time"] / s["count"], 1) if s["count"] > 0 else 0
        s["error_pct"] = round(s["errors"] / s["count"] * 100, 1) if s["count"] > 0 else 0
        s["throughput"] = round(s["count"] / (s["total_time"] / 1000), 2) if s["total_time"] > 0 else 0

    return stats


def link_jmeter_report():
    """Inject a link to the comparison report inside JMeter's standard index.html."""
    index_file = os.path.join(os.path.dirname(OUTPUT_FILE), "index.html")
    if os.path.exists(index_file):
        try:
            with open(index_file, "r") as f:
                content = f.read()
            
            # CSS snippet for a fancy glowing button
            btn_html = """
            <li style="padding: 10px 15px;">
                <a href="comparison_report.html" style="background-color: #1976d2; color: white; border-radius: 4px; text-align: center; font-weight: bold; padding: 8px 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    <i class="fa fa-bar-chart"></i> View DLoader Comparison
                </a>
            </li>
            """
            
            # Inject into the sidebar menu list
            if '<ul class="nav" id="side-menu">' in content:
                content = content.replace('<ul class="nav" id="side-menu">',
                                          '<ul class="nav" id="side-menu">\n' + btn_html, 1)
                with open(index_file, "w") as f:
                    f.write(content)
                print("Injected link into JMeter dashboard sidebar.")
        except Exception as e:
            print(f"Error modifying JMeter index.html: {e}")

def generate_html(stats):
    """Generate the comparison HTML report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    has_results = len(stats) > 0

    # Build performance summary per query per database
    perf_data = {}
    for q in QUERY_MAP:
        for db_entry in q["databases"]:
            label = db_entry["label"]
            if label in stats:
                perf_data[label] = stats[label]
            db_entry["escaped_code"] = html_lib.escape(db_entry.get("code", ""))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DLoader Benchmark Report</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #f8f9fa;
    --card: #ffffff;
    --border: #e9ecef;
    --text: #212529;
    --text-secondary: #6c757d;
    --mongo: #4caf50;
    --cassandra: #1976d2;
    --mysql: #ff9800;
    --differs: #e67e22;
    --radius: 10px;
    --shadow: 0 2px 12px rgba(0,0,0,0.06);
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
  }}

  .container {{
    max-width: 1200px;
    margin: 0 auto;
  }}

  .header {{
    text-align: center;
    margin-bottom: 2.5rem;
  }}

  .header h1 {{
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(135deg, #1976d2, #4caf50);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.25rem;
  }}

  .header .subtitle {{
    color: var(--text-secondary);
    font-size: 0.9rem;
  }}

  .header .timestamp {{
    color: var(--text-secondary);
    font-size: 0.8rem;
    margin-top: 0.25rem;
  }}

  /* Legend */
  .legend {{
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
  }}

  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
  }}

  /* Section titles */
  .section-title {{
    font-size: 1.2rem;
    font-weight: 600;
    margin: 2rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border);
  }}

  /* Query Map Table */
  .query-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background: var(--card);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
  }}

  .query-table thead th {{
    background: #f1f3f5;
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border);
  }}

  .query-table tbody td {{
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.875rem;
    vertical-align: middle;
  }}

  .query-table tbody tr:last-child td {{
    border-bottom: none;
  }}

  .query-table tbody tr:hover {{
    background: #f8f9fa;
  }}

  .query-id {{
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--text);
    min-width: 40px;
  }}

  .clickable-id {{
    cursor: pointer;
    color: #1976d2;
    text-decoration: underline;
  }}

  .clickable-id:hover {{
    color: #0d47a1;
  }}

  /* DB badges */
  .db-badge {{
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #fff;
    min-width: 90px;
    text-align: center;
  }}

  .db-badge.mongodb {{ background: var(--mongo); }}
  .db-badge.cassandra {{ background: var(--cassandra); }}
  .db-badge.mysql {{ background: var(--mysql); }}

  .operation-title {{
    font-weight: 500;
    color: var(--text);
    margin-bottom: 2px;
  }}

  .operation-desc {{
    color: var(--text-secondary);
    font-size: 0.82rem;
  }}

  .differs-badge {{
    display: inline-block;
    background: var(--differs);
    color: #fff;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 3px;
    margin-left: 6px;
    vertical-align: middle;
  }}

  .script-path {{
    font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }}

  /* Performance Table */
  .perf-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background: var(--card);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
    margin-top: 0.5rem;
  }}

  .perf-table thead th {{
    background: #f1f3f5;
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border);
  }}

  .perf-table thead th.num {{
    text-align: right;
  }}

  .perf-table tbody td {{
    padding: 0.65rem 1rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.875rem;
  }}

  .perf-table tbody td.num {{
    text-align: right;
    font-family: 'SF Mono', 'Menlo', monospace;
    font-size: 0.82rem;
  }}

  .perf-table tbody tr:last-child td {{
    border-bottom: none;
  }}

  .perf-table tbody tr:hover {{
    background: #f8f9fa;
  }}

  .best-value {{
    color: #2e7d32;
    font-weight: 600;
  }}

  .worst-value {{
    color: #c62828;
  }}

  /* Bar chart */
  .chart-section {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-top: 1rem;
  }}

  .chart-card {{
    background: var(--card);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 1.25rem;
  }}

  .chart-card h3 {{
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text);
  }}

  .bar-group {{
    margin-bottom: 0.75rem;
  }}

  .bar-label {{
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 3px;
  }}

  .bar-container {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .bar {{
    height: 22px;
    border-radius: 4px;
    min-width: 2px;
    transition: width 0.6s ease;
  }}

  .bar.mongodb {{ background: var(--mongo); }}
  .bar.cassandra {{ background: var(--cassandra); }}
  .bar.mysql {{ background: var(--mysql); }}

  .bar-value {{
    font-size: 0.78rem;
    font-family: 'SF Mono', monospace;
    color: var(--text-secondary);
    white-space: nowrap;
  }}

  /* Modal Styles */
  .modal-overlay {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.6);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }}

  .modal-overlay.active {{
    display: flex;
  }}

  .modal-content {{
    background: var(--card);
    width: 90%;
    max-width: 1200px;
    max-height: 90vh;
    border-radius: var(--radius);
    padding: 2rem;
    position: relative;
    overflow-y: auto;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  }}

  .modal-close {{
    position: absolute;
    top: 1.5rem;
    right: 2rem;
    font-size: 1.75rem;
    cursor: pointer;
    color: var(--text-secondary);
    background: none;
    border: none;
    padding: 0;
  }}

  .modal-close:hover {{
    color: var(--text);
  }}

  .code-section {{
    margin-top: 1.5rem;
  }}

  .code-section h4 {{
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}

  .code-block {{
    background: #282c34;
    color: #abb2bf;
    padding: 1.25rem;
    border-radius: 8px;
    font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
    font-size: 0.85rem;
    overflow-x: auto;
    white-space: pre;
    line-height: 1.4;
  }}
  
  .scripts-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }}

  /* Footer */
  .footer {{
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }}

  .footer .differs-note {{
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }}

  .footer .source {{
    font-size: 0.78rem;
    color: var(--text-secondary);
    font-family: 'SF Mono', monospace;
  }}

  @media (max-width: 768px) {{
    body {{ padding: 1rem; }}
    .chart-section {{ grid-template-columns: 1fr; }}
    .scripts-grid {{ grid-template-columns: 1fr; }}
    .query-table {{ font-size: 0.8rem; }}
  }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>BenchPress — DLoader Benchmark Report</h1>
    <div class="subtitle">SQL to NoSQL Performance Comparison · TPC-H Dataset</div>
    <div class="timestamp">Generated {now}</div>
  </div>

  <div class="legend">
    <span class="legend-item"><span class="legend-dot" style="background:var(--mongo)"></span> MongoDB</span>
    <span class="legend-item"><span class="legend-dot" style="background:var(--cassandra)"></span> Cassandra</span>
    <span class="legend-item"><span class="legend-dot" style="background:var(--mysql)"></span> MySQL</span>
  </div>

  <!-- ===== QUERY COMPARISON TABLE ===== -->
  <div class="section-title">Query Comparison</div>
  <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1rem;">Click on a Query ID to securely view the scripts run across the databases.</p>
  <table class="query-table">
    <thead>
      <tr>
        <th>Query</th>
        <th>Database</th>
        <th>Operation</th>
        <th>Script</th>
      </tr>
    </thead>
    <tbody>
"""

    # Build query comparison rows
    for q in QUERY_MAP:
        for i, db_entry in enumerate(q["databases"]):
            db_class = db_entry["db"].lower()
            differs_html = ' <span class="differs-badge">differs</span>' if db_entry["differs"] else ""
            query_cell = f'<td class="query-id" rowspan="3"><span class="clickable-id" onclick="openModal(\'{q["id"]}\')">{q["id"]}</span></td>' if i == 0 else ""

            html += f"""      <tr>
        {query_cell}<td><span class="db-badge {db_class}">{db_entry["db"]}</span></td>
        <td>
          <div class="operation-title">{q["title"]}{differs_html}</div>
          <div class="operation-desc">{db_entry["operation"]}</div>
        </td>
        <td class="script-path">{db_entry["script"]}</td>
      </tr>
"""

    html += """    </tbody>
  </table>
"""

    # ===== PERFORMANCE RESULTS TABLE =====
    if has_results:
        html += """
  <div class="section-title">Performance Results</div>
  <table class="perf-table">
    <thead>
      <tr>
        <th>Query</th>
        <th>Database</th>
        <th class="num">Samples</th>
        <th class="num">Avg (ms)</th>
        <th class="num">Min (ms)</th>
        <th class="num">Max (ms)</th>
        <th class="num">Throughput</th>
        <th class="num">Error %</th>
      </tr>
    </thead>
    <tbody>
"""
        for q in QUERY_MAP:
            # Find best avg for this query group
            avgs = []
            for db_entry in q["databases"]:
                if db_entry["label"] in perf_data:
                    avgs.append(perf_data[db_entry["label"]]["avg"])
            best_avg = min(avgs) if avgs else None
            worst_avg = max(avgs) if avgs else None

            for i, db_entry in enumerate(q["databases"]):
                label = db_entry["label"]
                db_class = db_entry["db"].lower()
                query_cell = f'<td class="query-id" rowspan="3">{q["id"]}</td>' if i == 0 else ""

                if label in perf_data:
                    d = perf_data[label]
                    avg_class = "num"
                    if d["avg"] == best_avg and len(avgs) > 1:
                        avg_class += ' best-value'
                    elif d["avg"] == worst_avg and len(avgs) > 1:
                        avg_class += ' worst-value'

                    html += f"""      <tr>
        {query_cell}<td><span class="db-badge {db_class}">{db_entry["db"]}</span></td>
        <td class="num">{d["count"]}</td>
        <td class="{avg_class}">{d["avg"]}</td>
        <td class="num">{d["min"]}</td>
        <td class="num">{d["max"]}</td>
        <td class="num">{d["throughput"]}/s</td>
        <td class="num">{d["error_pct"]}%</td>
      </tr>
"""
                else:
                    html += f"""      <tr>
        {query_cell}<td><span class="db-badge {db_class}">{db_entry["db"]}</span></td>
        <td colspan="6" style="color:var(--text-secondary);text-align:center">No data</td>
      </tr>
"""

        html += """    </tbody>
  </table>
"""

        # ===== BAR CHARTS =====
        html += """
  <div class="section-title">Response Time Comparison</div>
  <div class="chart-section">
"""
        for q in QUERY_MAP:
            # Get max avg for scaling bars
            max_avg = 1
            bars_data = []
            for db_entry in q["databases"]:
                label = db_entry["label"]
                if label in perf_data:
                    avg = perf_data[label]["avg"]
                    max_avg = max(max_avg, avg)
                    bars_data.append((db_entry["db"], avg))

            html += f"""    <div class="chart-card">
      <h3>{q["id"]} — {q["title"]}</h3>
"""
            for db_name, avg in bars_data:
                db_class = db_name.lower()
                width_pct = max((avg / max_avg) * 100, 2) if max_avg > 0 else 2
                html += f"""      <div class="bar-group">
        <div class="bar-label">{db_name}</div>
        <div class="bar-container">
          <div class="bar {db_class}" style="width:{width_pct}%"></div>
          <span class="bar-value">{avg} ms</span>
        </div>
      </div>
"""
            html += """    </div>
"""

        html += """  </div>
"""

    # ===== FOOTER =====
    html += f"""
  <div class="footer">
    <div class="differs-note">
      <span class="differs-badge">differs</span>
      <span>Cassandra's partition-key model required a different query approach for Q3 and Q4 compared to MongoDB and MySQL.</span>
    </div>
    <div class="source">Source: benchmark_nosql.jmx · TPC-H 1 GB dataset · 5 threads · 100 loops</div>
  </div>

</div>

<!-- ===== MODALS ===== -->
"""

    # Build modals
    for q in QUERY_MAP:
        html += f"""
<div id="modal-{q['id']}" class="modal-overlay">
  <div class="modal-content">
    <button class="modal-close" onclick="closeModal('{q['id']}')">&times;</button>
    <h2 style="margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; color: var(--text);">
      {q['id']} — {q['title']}
    </h2>
    <div class="scripts-grid">
"""
        for db_entry in q["databases"]:
            db_class = db_entry["db"].lower()
            html += f"""
      <div class="code-section">
        <h4><span class="db-badge {db_class}">{db_entry['db']}</span></h4>
        <div class="code-block">{db_entry['escaped_code']}</div>
      </div>
"""
        html += """
    </div>
  </div>
</div>
"""

    html += """
<script>
  function openModal(id) {
    document.getElementById('modal-' + id).classList.add('active');
    document.body.style.overflow = 'hidden'; // prevent background scrolling
  }

  function closeModal(id) {
    document.getElementById('modal-' + id).classList.remove('active');
    document.body.style.overflow = '';
  }

  // Close modals when clicking outside the content area
  window.onclick = function(event) {
    if (event.target.classList.contains('modal-overlay')) {
      event.target.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  // Close on ESC key
  document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") {
      const activeModals = document.querySelectorAll('.modal-overlay.active');
      activeModals.forEach(function(modal) {
        modal.classList.remove('active');
      });
      document.body.style.overflow = '';
    }
  });
</script>
</body>
</html>"""

    return html


def main():
    results_file = sys.argv[1] if len(sys.argv) > 1 else RESULTS_FILE
    output_file = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE

    print(f"Parsing results from {results_file}...")
    stats = parse_results(results_file)

    print(f"Generating comparison report...")
    html = generate_html(stats)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        f.write(html)

    print(f"✅ Comparison report generated: {output_file}")
    
    # Try to link it in the JMeter dashboard
    if os.path.basename(output_file) == "comparison_report.html":
        link_jmeter_report()


if __name__ == "__main__":
    main()
