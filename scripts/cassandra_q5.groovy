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

// Q5: Revenue aggregation - compute total revenue per order for a customer
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

String queryStr = 'SELECT order_id, extended_price, discount, tax FROM customer_orders WHERE customer_id = ' + customerId
ResultSet rs = session.execute(queryStr)

Map<Integer, Double> orderRevenue = new LinkedHashMap<Integer, Double>()
for (Row row : rs) {
    int orderId = row.getInt('order_id')
    try {
        java.math.BigDecimal ep = row.getBigDecimal('extended_price')
        java.math.BigDecimal disc = row.getBigDecimal('discount')
        java.math.BigDecimal tax = row.getBigDecimal('tax')
        if (ep != null && disc != null && tax != null) {
            double rev = ep.doubleValue() * (1.0 - disc.doubleValue()) * (1.0 + tax.doubleValue())
            orderRevenue.merge(orderId, rev, Double::sum)
        }
    } catch (Exception e) { /* skip */ }
}

double grandTotal = orderRevenue.values().stream().mapToDouble(Double::doubleValue).sum()
StringBuilder sb = new StringBuilder()
sb.append('Customer ').append(customerId).append(': ')
  .append(orderRevenue.size()).append(' orders\n')

int shown = 0
for (Map.Entry<Integer, Double> entry : orderRevenue.entrySet()) {
    if (shown++ < 5) {
        sb.append('  Order ').append(entry.getKey())
          .append(': ').append(String.format('%.2f', entry.getValue())).append('\n')
    }
}
sb.append('Grand Total Revenue: ').append(String.format('%.2f', grandTotal))

SampleResult.setResponseData(sb.toString(), 'UTF-8')
SampleResult.setSuccessful(true)
