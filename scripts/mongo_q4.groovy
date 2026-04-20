import com.mongodb.client.MongoClients
import com.mongodb.client.MongoClient
import com.mongodb.client.MongoCollection
import com.mongodb.client.MongoDatabase
import com.mongodb.client.FindIterable
import org.bson.Document
import java.util.Random

MongoClient mongoClient = (MongoClient) props.get('mongoClient')
if (mongoClient == null) {
    synchronized(props) {
        mongoClient = (MongoClient) props.get('mongoClient')
        if (mongoClient == null) {
            String connStr = 'mongodb://' + vars.get('MONGO_HOST') + ':' + vars.get('MONGO_PORT')
            mongoClient = MongoClients.create(connStr)
            props.put('mongoClient', mongoClient)
        }
    }
}

MongoDatabase database = mongoClient.getDatabase(vars.get('MONGO_DB'))
MongoCollection<Document> collection = database.getCollection('customers')

// Q4: Range query - find customers in a random region with customer_id range
String[] regions = ['AFRICA', 'AMERICA', 'ASIA', 'EUROPE', 'MIDDLE EAST'] as String[]
Random rand = new Random()
String selectedRegion = regions[rand.nextInt(regions.length)]

int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int startId = rand.nextInt(maxId - 1000) + 1
int endId = startId + 100

Document query = new Document('region', selectedRegion)
    .append('customer_id', new Document('$gte', startId).append('$lte', endId))

FindIterable<Document> results = collection.find(query)
    .projection(new Document('customer_id', 1).append('name', 1).append('region', 1))

int count = 0
for (Document doc : results) {
    count++
}

SampleResult.setResponseData('Region=' + selectedRegion +
    ', Range=[' + startId + '-' + endId + ']: Found ' + count + ' customers', 'UTF-8')
SampleResult.setSuccessful(true)
