import java.sql.*
import java.util.Random

// Reuse JDBC connection
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

// Q1: Simple point query - read customer by primary key with JOINs
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

String sql = 'SELECT c.c_custkey, c.c_name, n.n_name AS nation, r.r_name AS region ' +
    'FROM customer c ' +
    'JOIN nation n ON c.c_nationkey = n.n_nationkey ' +
    'JOIN region r ON n.n_regionkey = r.r_regionkey ' +
    'WHERE c.c_custkey = ?'

PreparedStatement pstmt = conn.prepareStatement(sql)
pstmt.setInt(1, customerId)
ResultSet rs = pstmt.executeQuery()

if (rs.next()) {
    SampleResult.setResponseData(
        'Customer found: id=' + rs.getInt('c_custkey') +
        ', name=' + rs.getString('c_name') +
        ', nation=' + rs.getString('nation') +
        ', region=' + rs.getString('region'), 'UTF-8')
    SampleResult.setSuccessful(true)
} else {
    SampleResult.setResponseData('Customer ' + customerId + ' not found', 'UTF-8')
    SampleResult.setSuccessful(true)
}
rs.close()
pstmt.close()
