import com.mongodb.client.MongoClients
import com.mongodb.client.MongoClient
import com.mongodb.client.MongoCollection
import com.mongodb.client.MongoDatabase
import com.mongodb.client.AggregateIterable
import org.bson.Document
import java.util.Arrays
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

// Q3: Aggregation - count orders grouped by order status for a random customer
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

List<Document> pipeline = Arrays.asList(
    new Document('$match', new Document('customer_id', customerId)),
    new Document('$unwind', '$orders'),
    new Document('$group', new Document('_id', '$orders.status')
        .append('order_count', new Document('$sum', 1))
        .append('total_value', new Document('$sum', '$orders.total_price')))
)

AggregateIterable<Document> results = collection.aggregate(pipeline)
StringBuilder sb = new StringBuilder()
sb.append('Customer ').append(customerId).append(' order summary:\n')
for (Document doc : results) {
    sb.append('  Status: ').append(doc.get('_id'))
      .append(', Count: ').append(doc.get('order_count'))
      .append(', Total: ').append(doc.get('total_value')).append('\n')
}

SampleResult.setResponseData(sb.toString(), 'UTF-8')
SampleResult.setSuccessful(true)
