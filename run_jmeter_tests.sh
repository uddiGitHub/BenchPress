#!/bin/bash

# Clean previous results if they exist
rm -rf results.jtl jmeter_reports
mkdir -p jmeter_reports

export JMETER_HOME=/opt/homebrew/Cellar/jmeter/5.6.3
export PATH=$JMETER_HOME/bin:$PATH

CLASSPATH="jmeter-libs/HdrHistogram-2.1.12.jar:jmeter-libs/bson-4.8.2.jar:jmeter-libs/config-1.4.1.jar:jmeter-libs/java-driver-core-shaded-4.13.0.jar:jmeter-libs/java-driver-shaded-guava-25.1-jre-graal-sub-1.jar:jmeter-libs/metrics-core-4.1.18.jar:jmeter-libs/mongodb-driver-core-4.8.2.jar:jmeter-libs/mongodb-driver-sync-4.8.2.jar:jmeter-libs/native-protocol-1.5.0.jar:jmeter-libs/reactive-streams-1.0.3.jar"

echo "Running JMeter NoSQL Benchmark..."
jmeter -n -t benchmark_nosql.jmx -l results.jtl -e -o jmeter_reports -Juser.classpath="$CLASSPATH"

echo "Benchmark complete! Reports generated in jmeter_reports/index.html"
