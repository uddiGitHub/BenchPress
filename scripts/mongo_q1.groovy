import com.mongodb.client.MongoClients
import com.mongodb.client.MongoClient
import com.mongodb.client.MongoCollection
import com.mongodb.client.MongoDatabase
import org.bson.Document
import java.util.Random

// Reuse connection across iterations (thread-safe singleton)
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

// Q1: Point query - retrieve a single customer document by customer_id
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

Document query = new Document('customer_id', customerId)
Document doc = collection.find(query).first()

if (doc != null) {
    String name = doc.getString('name')
    String nation = doc.getString('nation')
    String region = doc.getString('region')
    SampleResult.setResponseData(
        'Customer found: id=' + customerId + ', name=' + name +
        ', nation=' + nation + ', region=' + region, 'UTF-8')
    SampleResult.setSuccessful(true)
} else {
    SampleResult.setResponseData('Customer ' + customerId + ' not found', 'UTF-8')
    SampleResult.setSuccessful(true)
}
