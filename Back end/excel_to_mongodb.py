import pandas as pd
from pymongo import MongoClient

# Assuming you have an Excel file named 'your_excel_file.xlsx'
excel_file = 'output.xlsx'

# Load the Excel file into a DataFrame
df = pd.read_excel(excel_file)

# Connect to MongoDB server
client = MongoClient('mongodb://localhost:27017')

# Choose or create a database and a collection in MongoDB
db = client['immortals']
collection = db['patient_health']

# Convert DataFrame to a list of dictionaries for easy insertion
data_dicts = df.to_dict(orient='records')

# Insert data into MongoDB collection
collection.insert_many(data_dicts)

# Close the MongoDB connection
client.close()
