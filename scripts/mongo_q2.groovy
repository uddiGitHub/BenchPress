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

// Q2: Nested detail query - retrieve customer with all orders and lineitems unwound
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int customerId = rand.nextInt(maxId) + 1

// Aggregation pipeline: match customer, unwind orders, unwind lineitems
List<Document> pipeline = Arrays.asList(
    new Document('$match', new Document('customer_id', customerId)),
    new Document('$unwind', new Document('path', '$orders').append('preserveNullAndEmptyArrays', true)),
    new Document('$unwind', new Document('path', '$orders.lineitems').append('preserveNullAndEmptyArrays', true)),
    new Document('$project', new Document('customer_id', 1)
        .append('name', 1)
        .append('nation', 1)
        .append('region', 1)
        .append('orders.order_id', 1)
        .append('orders.status', 1)
        .append('orders.total_price', 1)
        .append('orders.order_date', 1)
        .append('orders.lineitems.line_number', 1)
        .append('orders.lineitems.quantity', 1)
        .append('orders.lineitems.extended_price', 1)
        .append('orders.lineitems.discount', 1)
        .append('orders.lineitems.return_flag', 1)
        .append('orders.lineitems.line_status', 1)
        .append('orders.lineitems.ship_date', 1))
)

AggregateIterable<Document> results = collection.aggregate(pipeline)
int count = 0
StringBuilder sb = new StringBuilder()
for (Document doc : results) {
    count++
    if (count <= 3) {
        sb.append(doc.toJson()).append('\n')
    }
}

SampleResult.setResponseData('Customer ' + customerId + ': Found ' + count +
    ' order-lineitem rows.\nSample:\n' + sb.toString(), 'UTF-8')
SampleResult.setSuccessful(true)
