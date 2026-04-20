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

// Q2: Join query - customer + orders + lineitems (equivalent to NoSQL nested read)
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

String sql = 'SELECT c.c_custkey, c.c_name, n.n_name AS nation, r.r_name AS region, ' +
    'o.o_orderkey, o.o_orderstatus, o.o_totalprice, o.o_orderdate, ' +
    'l.l_linenumber, l.l_quantity, l.l_extendedprice, l.l_discount, ' +
    'l.l_tax, l.l_returnflag, l.l_linestatus, l.l_shipdate ' +
    'FROM customer c ' +
    'JOIN nation n ON c.c_nationkey = n.n_nationkey ' +
    'JOIN region r ON n.n_regionkey = r.r_regionkey ' +
    'JOIN orders o ON c.c_custkey = o.o_custkey ' +
    'JOIN lineitem l ON o.o_orderkey = l.l_orderkey ' +
    'WHERE c.c_custkey = ?'

PreparedStatement pstmt = conn.prepareStatement(sql)
pstmt.setInt(1, customerId)
ResultSet rs = pstmt.executeQuery()

int rowCount = 0
double totalRevenue = 0.0
while (rs.next()) {
    rowCount++
    double ep = rs.getDouble('l_extendedprice')
    double disc = rs.getDouble('l_discount')
    totalRevenue += ep * (1.0 - disc)
}

SampleResult.setResponseData('Customer ' + customerId + ': ' + rowCount +
    ' order-lines (via JOIN), revenue=' + String.format('%.2f', totalRevenue), 'UTF-8')
SampleResult.setSuccessful(true)
rs.close()
pstmt.close()
