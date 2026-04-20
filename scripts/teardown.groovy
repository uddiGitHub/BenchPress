// Close MongoDB connection
try {
    def mongoClient = props.get('mongoClient')
    if (mongoClient != null) {
        mongoClient.close()
        props.remove('mongoClient')
        log.info('MongoDB connection closed.')
    }
} catch (Exception e) {
    log.warn('Error closing MongoDB: ' + e.getMessage())
}

// Close Cassandra session
try {
    def cassandraSession = props.get('cassandraSession')
    if (cassandraSession != null) {
        cassandraSession.close()
        props.remove('cassandraSession')
        log.info('Cassandra session closed.')
    }
} catch (Exception e) {
    log.warn('Error closing Cassandra: ' + e.getMessage())
}

// Close MySQL connection
try {
    def mysqlConn = props.get('mysqlConnection')
    if (mysqlConn != null && !mysqlConn.isClosed()) {
        mysqlConn.close()
        props.remove('mysqlConnection')
        log.info('MySQL connection closed.')
    }
} catch (Exception e) {
    log.warn('Error closing MySQL: ' + e.getMessage())
}

SampleResult.setResponseData('All connections closed.', 'UTF-8')
SampleResult.setSuccessful(true)
