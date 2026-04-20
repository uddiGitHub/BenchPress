/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 100.0, "KoPercent": 0.0};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9995333955472604, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "MySQL Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [0.0, 500, 1500, "Close All Connections"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q4 - Filter by Return Flag"], "isController": false}, {"data": [0.999, 500, 1500, "Cassandra Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [0.999, 500, 1500, "MongoDB Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q4 - Range Query: Customers by Region"], "isController": false}, {"data": [0.997, 500, 1500, "MongoDB Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q3 - Count Customer Orders"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q4 - Range Query: Customers by Region"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 7501, 0, 0.0, 31.565791227836062, 0, 2113, 14.0, 78.0, 85.0, 107.0, 148.135713721463, 31.548449812139584, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["MySQL Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 13.401999999999997, 0, 112, 9.0, 30.0, 38.89999999999998, 66.94000000000005, 48.91410682840931, 4.326032393367247, 0.0], "isController": false}, {"data": ["Close All Connections", 1, 0, 0.0, 2113.0, 2113, 2113, 2113.0, 2113.0, 2113.0, 2113.0, 0.473260766682442, 0.010629880501656412, 0.0], "isController": false}, {"data": ["Cassandra Q4 - Filter by Return Flag", 500, 0, 0.0, 2.184, 0, 31, 2.0, 3.0, 4.0, 8.990000000000009, 445.23597506678544, 28.33944373330365, 0.0], "isController": false}, {"data": ["Cassandra Q1 - Read Customer by ID", 500, 0, 0.0, 3.650000000000003, 0, 575, 1.0, 2.0, 3.0, 6.990000000000009, 283.7684449489217, 24.19458534335982, 0.0], "isController": false}, {"data": ["MySQL Q2 - Read Customer Orders Detail", 500, 0, 0.0, 20.139999999999997, 0, 159, 16.0, 40.0, 57.89999999999998, 110.74000000000024, 48.55311711011847, 2.786683397261604, 0.0], "isController": false}, {"data": ["MongoDB Q2 - Read Customer Orders Detail", 500, 0, 0.0, 76.71000000000002, 51, 511, 72.0, 84.0, 88.0, 159.92000000000007, 14.306560988869496, 18.659276284729177, 0.0], "isController": false}, {"data": ["MySQL Q1 - Read Customer by ID", 500, 0, 0.0, 11.839999999999993, 0, 305, 7.0, 26.0, 37.0, 59.97000000000003, 47.160913035276366, 3.7360285795132993, 0.0], "isController": false}, {"data": ["Cassandra Q5 - Revenue Aggregation", 500, 0, 0.0, 3.0060000000000002, 0, 84, 2.0, 4.0, 5.0, 11.980000000000018, 457.45654162854527, 61.108867509149135, 0.0], "isController": false}, {"data": ["MongoDB Q5 - Revenue Aggregation", 500, 0, 0.0, 82.38000000000005, 64, 192, 81.0, 93.90000000000003, 99.0, 135.96000000000004, 14.535306258902875, 8.423976487325213, 0.0], "isController": false}, {"data": ["MongoDB Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 72.986, 49, 195, 71.0, 82.0, 86.0, 126.97000000000003, 14.497375974948534, 1.4893788599263535, 0.0], "isController": false}, {"data": ["Cassandra Q2 - Read Customer Orders Detail", 500, 0, 0.0, 2.5040000000000013, 0, 54, 2.0, 4.0, 5.0, 9.990000000000009, 418.41004184100416, 51.5567795502092, 0.0], "isController": false}, {"data": ["MongoDB Q4 - Range Query: Customers by Region", 500, 0, 0.0, 78.99800000000002, 63, 174, 76.0, 89.0, 94.94999999999999, 141.0, 14.507471347744088, 0.7683009484259393, 0.0], "isController": false}, {"data": ["MongoDB Q1 - Read Customer by ID", 500, 0, 0.0, 43.53799999999998, 0, 1174, 38.0, 65.0, 71.0, 355.3600000000024, 13.928740563278268, 1.5948952036381872, 0.0], "isController": false}, {"data": ["MySQL Q5 - Revenue Aggregation", 500, 0, 0.0, 43.58600000000003, 9, 309, 38.5, 68.0, 87.0, 152.99, 49.120738775911185, 14.978947158365262, 0.0], "isController": false}, {"data": ["Cassandra Q3 - Count Customer Orders", 500, 0, 0.0, 1.9659999999999989, 0, 26, 2.0, 3.0, 4.0, 8.990000000000009, 435.54006968641113, 22.33333787020906, 0.0], "isController": false}, {"data": ["MySQL Q4 - Range Query: Customers by Region", 500, 0, 0.0, 12.433999999999989, 0, 89, 9.0, 28.0, 32.94999999999999, 64.98000000000002, 49.01960784313725, 2.644282322303922, 0.0], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": []}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 7501, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
