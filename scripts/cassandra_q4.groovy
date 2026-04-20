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

// Q4: Read orders for a customer and filter by return_flag
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1
String[] flags = ['R', 'A', 'N'] as String[]
String targetFlag = flags[rand.nextInt(flags.length)]

String queryStr = 'SELECT order_id, line_number, return_flag, quantity, extended_price FROM customer_orders WHERE customer_id = ' + customerId
ResultSet rs = session.execute(queryStr)

int matchCount = 0
double totalQty = 0.0
for (Row row : rs) {
    String flag = row.getString('return_flag')
    if (targetFlag.equals(flag)) {
        matchCount++
        try {
            java.math.BigDecimal qty = row.getBigDecimal('quantity')
            if (qty != null) totalQty += qty.doubleValue()
        } catch (Exception e) { /* skip */ }
    }
}

SampleResult.setResponseData('Customer ' + customerId +
    ', return_flag=' + targetFlag + ': ' + matchCount +
    ' matching lines, total_qty=' + String.format('%.2f', totalQty), 'UTF-8')
SampleResult.setSuccessful(true)
