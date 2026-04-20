import com.datastax.oss.driver.api.core.CqlSession
import com.datastax.oss.driver.api.core.cql.ResultSet
import com.datastax.oss.driver.api.core.cql.Row
import java.net.InetSocketAddress
import java.util.Random

CqlSession session = (CqlSession) props.get('cassandraSession')
if (session == null) {
    synchronized(props) {
        session = (CqlSession) props.get('cassandraSession')
        if (session == null) {
            session = CqlSession.builder()
                .addContactPoint(new InetSocketAddress(
                    vars.get('CASSANDRA_HOST'),
                    Integer.parseInt(vars.get('CASSANDRA_PORT'))))
                .withLocalDatacenter('datacenter1')
                .withKeyspace(vars.get('CASSANDRA_KEYSPACE'))
                .build()
            props.put('cassandraSession', session)
        }
    }
}

// Q2: Detail query - retrieve ALL order lines for a specific customer
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

String queryStr = 'SELECT * FROM customer_orders WHERE customer_id = ' + customerId
ResultSet rs = session.execute(queryStr)

int rowCount = 0
double totalRevenue = 0.0
StringBuilder sb = new StringBuilder()
for (Row row : rs) {
    rowCount++
    try {
        java.math.BigDecimal ep = row.getBigDecimal('extended_price')
        java.math.BigDecimal disc = row.getBigDecimal('discount')
        if (ep != null && disc != null) {
            totalRevenue += ep.doubleValue() * (1.0 - disc.doubleValue())
        }
    } catch (Exception e) { /* skip row on error */ }
    if (rowCount <= 3) {
        sb.append('  order_id=').append(row.getInt('order_id'))
          .append(', line=').append(row.getInt('line_number'))
          .append(', status=').append(row.getString('status')).append('\n')
    }
}

SampleResult.setResponseData('Customer ' + customerId + ': ' + rowCount +
    ' order-lines, revenue=' + String.format('%.2f', totalRevenue) +
    '\nSample:\n' + sb.toString(), 'UTF-8')
SampleResult.setSuccessful(true)
