
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['immortals']
collection = db['patient']
print(type(db))
print(type(collection))