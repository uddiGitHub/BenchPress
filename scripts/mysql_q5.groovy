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

// Q5: Complex analytical - compute revenue per order for a batch of customers
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int startId = rand.nextInt(maxId - 50) + 1
int endId = startId + 10

String sql = 'SELECT c.c_custkey, c.c_name, o.o_orderkey, ' +
    'SUM(l.l_extendedprice * (1 - l.l_discount) * (1 + l.l_tax)) AS revenue ' +
    'FROM customer c ' +
    'JOIN orders o ON c.c_custkey = o.o_custkey ' +
    'JOIN lineitem l ON o.o_orderkey = l.l_orderkey ' +
    'WHERE c.c_custkey BETWEEN ? AND ? ' +
    'GROUP BY c.c_custkey, c.c_name, o.o_orderkey ' +
    'ORDER BY revenue DESC'

PreparedStatement pstmt = conn.prepareStatement(sql)
pstmt.setInt(1, startId)
pstmt.setInt(2, endId)
ResultSet rs = pstmt.executeQuery()

StringBuilder sb = new StringBuilder()
sb.append('Revenue for customers ').append(startId).append('-').append(endId).append(':\n')
int count = 0
double grandTotal = 0.0
while (rs.next()) {
    count++
    double rev = rs.getDouble('revenue')
    grandTotal += rev
    if (count <= 5) {
        sb.append('  ').append(rs.getString('c_name'))
          .append(', order ').append(rs.getInt('o_orderkey'))
          .append(': ').append(String.format('%.2f', rev)).append('\n')
    }
}
sb.append('Total orders: ').append(count)
  .append(', Grand Total: ').append(String.format('%.2f', grandTotal))

SampleResult.setResponseData(sb.toString(), 'UTF-8')
SampleResult.setSuccessful(true)
rs.close()
pstmt.close()
