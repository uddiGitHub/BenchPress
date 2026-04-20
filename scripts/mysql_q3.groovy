import java.sql.*
import java.util.Random

Connection conn = (Connection) props.get('mysqlConnection')
if (conn == null || conn.isClosed()) {
    synchronized(props) {
        conn = (Connection) props.get('mysqlConnection')
        if (conn == null || conn.isClosed()) {
            Class.forName('com.mysql.cj.jdbc.Driver')
            String url = 'jdbc:mysql://' + vars.get('MYSQL_HOST') + ':' + vars.get('MYSQL_PORT') + '/' + vars.get('MYSQL_DB')
            conn = DriverManager.getConnection(url, vars.get('MYSQL_USER'), vars.get('MYSQL_PASSWORD'))
            props.put('mysqlConnection', conn)
        }
    }
}

// Q3: Aggregation - count orders by status for a given customer
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

String sql = 'SELECT o.o_orderstatus, COUNT(*) AS order_count, SUM(o.o_totalprice) AS total_value ' +
    'FROM orders o WHERE o.o_custkey = ? GROUP BY o.o_orderstatus'

PreparedStatement pstmt = conn.prepareStatement(sql)
pstmt.setInt(1, customerId)
ResultSet rs = pstmt.executeQuery()

StringBuilder sb = new StringBuilder()
sb.append('Customer ').append(customerId).append(' order summary:\n')
while (rs.next()) {
    sb.append('  Status: ').append(rs.getString('o_orderstatus'))
      .append(', Count: ').append(rs.getInt('order_count'))
      .append(', Total: ').append(rs.getDouble('total_value')).append('\n')
}

SampleResult.setResponseData(sb.toString(), 'UTF-8')
SampleResult.setSuccessful(true)
rs.close()
pstmt.close()
