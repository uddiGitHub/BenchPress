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

// Q3: Aggregation - count distinct orders for a customer
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

String queryStr = 'SELECT order_id, line_number FROM customer_orders WHERE customer_id = ' + customerId
ResultSet rs = session.execute(queryStr)

Set<Integer> uniqueOrders = new HashSet<Integer>()
int totalLines = 0
for (Row row : rs) {
    uniqueOrders.add(row.getInt('order_id'))
    totalLines++
}

SampleResult.setResponseData('Customer ' + customerId +
    ': ' + uniqueOrders.size() + ' unique orders, ' +
    totalLines + ' total line items', 'UTF-8')
SampleResult.setSuccessful(true)
