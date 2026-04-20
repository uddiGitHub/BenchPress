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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9994667377682975, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "MySQL Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [0.0, 500, 1500, "Close All Connections"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q4 - Filter by Return Flag"], "isController": false}, {"data": [0.999, 500, 1500, "Cassandra Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [0.998, 500, 1500, "MongoDB Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q4 - Range Query: Customers by Region"], "isController": false}, {"data": [0.997, 500, 1500, "MongoDB Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q3 - Count Customer Orders"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q4 - Range Query: Customers by Region"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 7501, 0, 0.0, 28.972270363951413, 0, 2105, 10.0, 77.0, 82.0, 92.0, 160.4011632879993, 34.791991602782055, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["MySQL Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 10.167999999999992, 0, 78, 7.0, 23.0, 28.94999999999999, 44.99000000000001, 65.76351440220965, 6.033288668946469, 0.0], "isController": false}, {"data": ["Close All Connections", 1, 0, 0.0, 2105.0, 2105, 2105, 2105.0, 2105.0, 2105.0, 2105.0, 0.4750593824228028, 0.010670279097387174, 0.0], "isController": false}, {"data": ["Cassandra Q4 - Filter by Return Flag", 500, 0, 0.0, 2.218, 0, 31, 2.0, 3.0, 4.0, 5.0, 440.52863436123346, 28.02863436123348, 0.0], "isController": false}, {"data": ["Cassandra Q1 - Read Customer by ID", 500, 0, 0.0, 3.494000000000002, 0, 540, 1.0, 2.0, 3.0, 4.0, 288.0184331797235, 24.03716337845622, 0.0], "isController": false}, {"data": ["MySQL Q2 - Read Customer Orders Detail", 500, 0, 0.0, 15.799999999999994, 0, 78, 13.0, 35.0, 44.94999999999999, 55.99000000000001, 65.3765690376569, 3.733104242939331, 0.0], "isController": false}, {"data": ["MongoDB Q2 - Read Customer Orders Detail", 500, 0, 0.0, 74.86600000000008, 40, 665, 72.0, 80.0, 83.0, 89.99000000000001, 14.667918329030744, 19.82122786977822, 0.0], "isController": false}, {"data": ["MySQL Q1 - Read Customer by ID", 500, 0, 0.0, 7.785999999999995, 0, 320, 3.5, 18.0, 22.94999999999999, 35.99000000000001, 62.758880381573995, 4.957828974206101, 0.0], "isController": false}, {"data": ["Cassandra Q5 - Revenue Aggregation", 500, 0, 0.0, 2.801999999999999, 0, 67, 2.0, 4.0, 4.0, 6.0, 451.6711833785004, 65.0900519421861, 0.0], "isController": false}, {"data": ["MongoDB Q5 - Revenue Aggregation", 500, 0, 0.0, 80.61000000000007, 52, 135, 80.0, 92.0, 95.94999999999999, 124.84000000000015, 14.99970000599988, 8.687961006404871, 0.0], "isController": false}, {"data": ["MongoDB Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 70.77599999999998, 41, 92, 70.0, 79.0, 82.0, 87.0, 14.940090238145038, 1.5052724512206055, 0.0], "isController": false}, {"data": ["Cassandra Q2 - Read Customer Orders Detail", 500, 0, 0.0, 2.43, 0, 53, 2.0, 3.0, 4.0, 5.0, 415.6275976724855, 52.19454618661679, 0.0], "isController": false}, {"data": ["MongoDB Q4 - Range Query: Customers by Region", 500, 0, 0.0, 76.03599999999999, 50, 159, 75.0, 84.0, 87.0, 107.86000000000013, 14.957520641378485, 0.7936250112181406, 0.0], "isController": false}, {"data": ["MongoDB Q1 - Read Customer by ID", 500, 0, 0.0, 40.54400000000002, 1, 938, 34.0, 66.0, 70.0, 78.0, 14.390973981119041, 1.6479913798065853, 0.0], "isController": false}, {"data": ["MySQL Q5 - Revenue Aggregation", 500, 0, 0.0, 33.31399999999999, 5, 99, 31.0, 54.0, 61.0, 80.99000000000001, 66.13756613756614, 20.173378596230158, 0.0], "isController": false}, {"data": ["Cassandra Q3 - Count Customer Orders", 500, 0, 0.0, 1.8960000000000024, 0, 27, 2.0, 3.0, 3.0, 4.990000000000009, 431.40638481449525, 22.1306419866264, 0.0], "isController": false}, {"data": ["MySQL Q4 - Range Query: Customers by Region", 500, 0, 0.0, 7.691999999999997, 0, 45, 4.0, 18.0, 24.0, 34.97000000000003, 65.98046978094483, 3.574672365729744, 0.0], "isController": false}]}, function(index, item){
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
