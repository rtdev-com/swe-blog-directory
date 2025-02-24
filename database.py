from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class MongoDBClient:
    def __init__(self, uri, db_name, collection_name):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        # Create a new client and connect to the server
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
        except Exception as e:
            print(e)

    def insert_documents(self, documents):
        try:
            result = self.collection.insert_many(documents)
            print(f"Documents inserted with _ids: {result.inserted_ids}")
        except Exception as e:
            print(e)

    def insert_document(self, document):
        try:
            result = self.collection.insert_one(document)
            print(f"Document inserted with _id: {result.inserted_id}")
        except Exception as e:
            print(e)

    def get_full_collection(self):
        try:
            cursor = self.collection.find()
            documents = list(cursor)
            for doc in documents:
                del doc['_id']
            return documents
        except Exception as e:
            print(e)

