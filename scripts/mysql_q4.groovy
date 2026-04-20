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

// Q4: Range query - find customers in a specific region within a customer_id range
String[] regions = ['AFRICA', 'AMERICA', 'ASIA', 'EUROPE', 'MIDDLE EAST'] as String[]
Random rand = new Random()
String selectedRegion = regions[rand.nextInt(regions.length)]
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int startId = rand.nextInt(maxId - 1000) + 1
int endId = startId + 100

String sql = 'SELECT c.c_custkey, c.c_name, r.r_name AS region ' +
    'FROM customer c ' +
    'JOIN nation n ON c.c_nationkey = n.n_nationkey ' +
    'JOIN region r ON n.n_regionkey = r.r_regionkey ' +
    'WHERE r.r_name = ? AND c.c_custkey BETWEEN ? AND ?'

PreparedStatement pstmt = conn.prepareStatement(sql)
pstmt.setString(1, selectedRegion)
pstmt.setInt(2, startId)
pstmt.setInt(3, endId)
ResultSet rs = pstmt.executeQuery()

int count = 0
while (rs.next()) { count++ }

SampleResult.setResponseData('Region=' + selectedRegion +
    ', Range=[' + startId + '-' + endId + ']: Found ' + count + ' customers', 'UTF-8')
SampleResult.setSuccessful(true)
rs.close()
pstmt.close()
