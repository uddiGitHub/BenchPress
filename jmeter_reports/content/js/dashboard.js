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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9998666844420744, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "MySQL Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [0.0, 500, 1500, "Close All Connections"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q4 - Filter by Return Flag"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q4 - Range Query: Customers by Region"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q3 - Count Customer Orders"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q4 - Range Query: Customers by Region"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 7501, 0, 0.0, 13.006132515664646, 0, 2098, 3.0, 35.0, 38.0, 43.0, 328.78933987902167, 70.75309602930218, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["MySQL Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 3.3639999999999994, 0, 19, 2.0, 7.900000000000034, 10.0, 16.0, 159.28639694170118, 14.490395528034407, 0.0], "isController": false}, {"data": ["Close All Connections", 1, 0, 0.0, 2098.0, 2098, 2098, 2098.0, 2098.0, 2098.0, 2098.0, 0.47664442326024786, 0.010705880600571973, 0.0], "isController": false}, {"data": ["Cassandra Q4 - Filter by Return Flag", 500, 0, 0.0, 0.7300000000000006, 0, 20, 1.0, 1.0, 1.0, 2.0, 791.1392405063291, 50.31923704509494, 0.0], "isController": false}, {"data": ["Cassandra Q1 - Read Customer by ID", 500, 0, 0.0, 1.3839999999999992, 0, 333, 0.0, 1.0, 1.0, 1.0, 494.5598417408507, 41.9709368818002, 0.0], "isController": false}, {"data": ["MySQL Q2 - Read Customer Orders Detail", 500, 0, 0.0, 7.044, 0, 26, 5.0, 15.900000000000034, 18.94999999999999, 24.0, 158.37820715869498, 9.13211217136522, 0.0], "isController": false}, {"data": ["MongoDB Q2 - Read Customer Orders Detail", 500, 0, 0.0, 33.82200000000003, 25, 97, 33.0, 38.0, 41.0, 51.99000000000001, 31.5000315000315, 41.76196656665407, 0.0], "isController": false}, {"data": ["MySQL Q1 - Read Customer by ID", 500, 0, 0.0, 2.8080000000000016, 0, 185, 1.0, 6.0, 8.0, 12.0, 149.655791679138, 11.866652012870398, 0.0], "isController": false}, {"data": ["Cassandra Q5 - Revenue Aggregation", 500, 0, 0.0, 0.9699999999999995, 0, 44, 1.0, 1.0, 2.0, 3.0, 815.6606851549756, 114.86955801386624, 0.0], "isController": false}, {"data": ["MongoDB Q5 - Revenue Aggregation", 500, 0, 0.0, 36.38000000000001, 27, 74, 36.0, 41.0, 43.0, 50.0, 31.709791983764585, 18.369073737157535, 0.0], "isController": false}, {"data": ["MongoDB Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 33.75200000000002, 25, 83, 33.0, 38.0, 41.0, 65.97000000000003, 31.635558367605192, 3.262231592059475, 0.0], "isController": false}, {"data": ["Cassandra Q2 - Read Customer Orders Detail", 500, 0, 0.0, 0.9419999999999998, 0, 30, 1.0, 2.0, 2.0, 3.990000000000009, 736.3770250368188, 91.93926040132547, 0.0], "isController": false}, {"data": ["MongoDB Q4 - Range Query: Customers by Region", 500, 0, 0.0, 34.91599999999998, 27, 55, 34.5, 39.0, 40.0, 48.99000000000001, 31.663605851434358, 1.679222440789057, 0.0], "isController": false}, {"data": ["MongoDB Q1 - Read Customer by ID", 500, 0, 0.0, 18.979999999999997, 1, 385, 18.0, 31.0, 33.0, 38.99000000000001, 30.807147258163894, 3.528862446087492, 0.0], "isController": false}, {"data": ["MySQL Q5 - Revenue Aggregation", 500, 0, 0.0, 12.229999999999999, 2, 32, 12.0, 21.0, 23.0, 29.0, 160.3077909586406, 48.902016872394995, 0.0], "isController": false}, {"data": ["Cassandra Q3 - Count Customer Orders", 500, 0, 0.0, 0.724, 0, 17, 1.0, 1.0, 2.0, 2.0, 770.4160246533128, 39.536486421417564, 0.0], "isController": false}, {"data": ["MySQL Q4 - Range Query: Customers by Region", 500, 0, 0.0, 2.876, 0, 20, 2.0, 7.0, 9.0, 14.980000000000018, 159.8976654940838, 8.645716741285577, 0.0], "isController": false}]}, function(index, item){
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
