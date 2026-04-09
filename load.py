import os
from dotenv import load_dotenv

load_dotenv()

def load_to_mongodb(df, collection_name="customers"):
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI not set in .env file")

    df.write \
        .format("mongodb") \
        .option("spark.mongodb.connection.uri", uri) \
        .option("spark.mongodb.database", "tpch") \
        .option("spark.mongodb.collection", collection_name) \
        .mode("overwrite") \
        .save()