import com.datastax.oss.driver.api.core.CqlSession
import com.datastax.oss.driver.api.core.cql.ResultSet
import com.datastax.oss.driver.api.core.cql.Row
import java.net.InetSocketAddress
import java.util.Random

// Reuse CQL session across iterations
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

// Q1: Point query - retrieve first row for a given customer_id (partition key)
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

String queryStr = 'SELECT customer_id, name, nation, region FROM customer_orders WHERE customer_id = ' + customerId + ' LIMIT 1'
ResultSet rs = session.execute(queryStr)
Row row = rs.one()

if (row != null) {
    SampleResult.setResponseData(
        'Customer found: id=' + row.getInt('customer_id') +
        ', name=' + row.getString('name') +
        ', nation=' + row.getString('nation') +
        ', region=' + row.getString('region'), 'UTF-8')
    SampleResult.setSuccessful(true)
} else {
    SampleResult.setResponseData('Customer ' + customerId + ' not found', 'UTF-8')
    SampleResult.setSuccessful(true)
}
