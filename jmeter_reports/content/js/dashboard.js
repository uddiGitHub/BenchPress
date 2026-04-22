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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9994000799893348, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "MySQL Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [0.0, 500, 1500, "Close All Connections"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q4 - Filter by Return Flag"], "isController": false}, {"data": [0.999, 500, 1500, "Cassandra Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [0.999, 500, 1500, "MongoDB Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q3 - Aggregation: Orders by Status"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q2 - Read Customer Orders Detail"], "isController": false}, {"data": [1.0, 500, 1500, "MongoDB Q4 - Range Query: Customers by Region"], "isController": false}, {"data": [0.995, 500, 1500, "MongoDB Q1 - Read Customer by ID"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q5 - Revenue Aggregation"], "isController": false}, {"data": [1.0, 500, 1500, "Cassandra Q3 - Count Customer Orders"], "isController": false}, {"data": [1.0, 500, 1500, "MySQL Q4 - Range Query: Customers by Region"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 7501, 0, 0.0, 29.811358485535088, 0, 2112, 10.0, 78.0, 83.0, 93.0, 156.34900783725195, 33.1348332043626, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["MySQL Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 9.23600000000001, 0, 50, 6.0, 22.0, 27.0, 41.0, 63.66993505666624, 5.9167028126193815, 0.0], "isController": false}, {"data": ["Close All Connections", 1, 0, 0.0, 2112.0, 2112, 2112, 2112.0, 2112.0, 2112.0, 2112.0, 0.4734848484848485, 0.01063491358901515, 0.0], "isController": false}, {"data": ["Cassandra Q4 - Filter by Return Flag", 500, 0, 0.0, 2.0540000000000007, 0, 33, 2.0, 3.0, 3.0, 5.990000000000009, 469.4835680751174, 29.832379694835684, 0.0], "isController": false}, {"data": ["Cassandra Q1 - Read Customer by ID", 500, 0, 0.0, 3.222000000000001, 0, 539, 1.0, 2.0, 2.0, 3.990000000000009, 298.32935560859187, 24.77765140214797, 0.0], "isController": false}, {"data": ["MySQL Q2 - Read Customer Orders Detail", 500, 0, 0.0, 17.652000000000005, 0, 73, 15.0, 37.0, 42.0, 61.99000000000001, 63.30716637123322, 3.651042985565966, 0.0], "isController": false}, {"data": ["MongoDB Q2 - Read Customer Orders Detail", 500, 0, 0.0, 76.28400000000002, 46, 1214, 73.0, 80.0, 84.0, 251.40000000000146, 14.22070534698521, 18.16131279330205, 0.0], "isController": false}, {"data": ["MySQL Q1 - Read Customer by ID", 500, 0, 0.0, 6.838, 0, 329, 3.0, 16.0, 21.94999999999999, 33.97000000000003, 60.78288353999513, 4.82511624726477, 0.0], "isController": false}, {"data": ["Cassandra Q5 - Revenue Aggregation", 500, 0, 0.0, 2.8479999999999994, 0, 88, 2.0, 4.0, 4.0, 6.0, 483.55899419729207, 66.75286357591877, 0.0], "isController": false}, {"data": ["MongoDB Q5 - Revenue Aggregation", 500, 0, 0.0, 82.2559999999999, 44, 107, 82.0, 93.0, 96.0, 103.0, 14.752308736317234, 8.550605259566872, 0.0], "isController": false}, {"data": ["MongoDB Q3 - Aggregation: Orders by Status", 500, 0, 0.0, 71.61800000000004, 45, 98, 71.0, 80.0, 82.0, 89.99000000000001, 14.708910658076663, 1.5436886822286942, 0.0], "isController": false}, {"data": ["Cassandra Q2 - Read Customer Orders Detail", 500, 0, 0.0, 2.2560000000000016, 0, 56, 2.0, 3.0, 4.0, 6.980000000000018, 436.3001745200698, 54.46849776396161, 0.0], "isController": false}, {"data": ["MongoDB Q4 - Range Query: Customers by Region", 500, 0, 0.0, 77.29999999999994, 44, 105, 77.0, 86.90000000000003, 89.94999999999999, 99.0, 14.728408153646754, 0.7842589677595145, 0.0], "isController": false}, {"data": ["MongoDB Q1 - Read Customer by ID", 500, 0, 0.0, 46.05799999999999, 1, 1607, 36.0, 67.0, 72.0, 439.3900000000033, 13.983667076854235, 1.6004197722060634, 0.0], "isController": false}, {"data": ["MySQL Q5 - Revenue Aggregation", 500, 0, 0.0, 35.482, 7, 95, 33.0, 58.0, 65.0, 79.0, 64.13545407901488, 19.56619881189071, 0.0], "isController": false}, {"data": ["Cassandra Q3 - Count Customer Orders", 500, 0, 0.0, 1.766000000000001, 0, 27, 2.0, 2.0, 3.0, 8.0, 458.295142071494, 23.48404560036664, 0.0], "isController": false}, {"data": ["MySQL Q4 - Range Query: Customers by Region", 500, 0, 0.0, 8.136000000000003, 0, 44, 4.0, 21.0, 25.0, 36.98000000000002, 64.00409626216077, 3.4665968621991805, 0.0], "isController": false}]}, function(index, item){
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
