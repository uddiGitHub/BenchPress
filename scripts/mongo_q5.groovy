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

// Q5: Complex analytical - compute total revenue per customer
Random rand = new Random()
int maxId = Integer.parseInt(vars.get('MAX_CUSTOMER_ID'))
int startId = rand.nextInt(maxId - 50) + 1
int endId = startId + 10

List<Document> pipeline = Arrays.asList(
    new Document('$match', new Document('customer_id',
        new Document('$gte', startId).append('$lte', endId))),
    new Document('$unwind', '$orders'),
    new Document('$unwind', '$orders.lineitems'),
    new Document('$group', new Document('_id',
        new Document('customer_id', '$customer_id').append('name', '$name'))
        .append('total_revenue', new Document('$sum',
            new Document('$multiply', Arrays.asList(
                '$orders.lineitems.extended_price',
                new Document('$subtract', Arrays.asList(1, '$orders.lineitems.discount'))
            ))))
        .append('total_orders', new Document('$sum', 1))),
    new Document('$sort', new Document('total_revenue', -1))
)

AggregateIterable<Document> results = collection.aggregate(pipeline)
StringBuilder sb = new StringBuilder()
sb.append('Revenue for customers ').append(startId).append('-').append(endId).append(':\n')
int count = 0
for (Document doc : results) {
    count++
    Document id = (Document) doc.get('_id')
    sb.append('  ').append(id.get('name'))
      .append(': revenue=').append(doc.get('total_revenue'))
      .append(', items=').append(doc.get('total_orders')).append('\n')
}

SampleResult.setResponseData(sb.toString() + 'Total customers: ' + count, 'UTF-8')
SampleResult.setSuccessful(true)
