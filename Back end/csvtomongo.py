import pandas as pd
from pymongo import MongoClient

def read_csv_with_exception(file_path):
    try:
        df = pd.read_csv(file_path, header=None)
        return df
    except FileNotFoundError:
        print(f"Error: File not found at path {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def split_and_rename_columns(df, new_column_name):
    df = df[0].str.split('_', expand=True)
    df.columns = ['name', 'date', 'time', 'place', new_column_name]
    return df

def update_mongo_with_health_data(df, collection):
    for index, row in df.iterrows():
        patient_id = row['name']
        health_data = {
            'blood_group': row.get('blood group'),
            'blood_pressure': row.get('blood pressure'),
            'blood_sugar': row.get('sugar level'),
            'height': row.get('height'),
            'spo2': row.get('spo2'),
            'weight': row.get('weight')
        }
        # Remove None values from health data
        health_data = {k: v for k, v in health_data.items() if pd.notna(v)}
        
        collection.update_one(
            {'patient_id': patient_id},
            {'$set': {'health': health_data}},
            upsert=True  # Insert new document if patient_id not found
        )

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['immortals']
collection = db['patient']

# CSV file paths
csv_files = {
    'blood_details': ('./patient_details/Blood_details.csv', 'blood group'),
    'blood_pressure': ('./patient_details/Blood_pressure.csv', 'blood pressure'),
    'blood_sugar': ('./patient_details/Blood_suger.csv', 'sugar level'),
    'height': ('./patient_details/Height.csv', 'height'),
    'spo2': ('./patient_details/spo2.csv', 'spo2'),
    'weight': ('./patient_details/Weight.csv', 'weight')
}

# Dictionary to hold dataframes
dfs = {}

# Iterate over CSV files
for file_name, (file_path, new_column_name) in csv_files.items():
    df = read_csv_with_exception(file_path)
    if df is not None:
        df = split_and_rename_columns(df, new_column_name)
        dfs[file_name] = df

# Check if any of the DataFrames is None before proceeding
if len(dfs) != len(csv_files):
    print("Error: One or more CSV files failed to load. Please check the file paths.")
else:
    # Merge all dataframes on common columns
    merged_df = dfs['blood_details']
    for key in dfs:
        if key != 'blood_details':
            merged_df = pd.merge(merged_df, dfs[key], on=['name', 'date', 'time', 'place'], how='outer')

    try:
        merged_df.to_excel('output.xlsx', index=False)
        print("Output successfully saved to 'output.xlsx'")
    except Exception as e:
        print(f"An error occurred while saving the output to Excel: {e}")

    # Update MongoDB with health data
    update_mongo_with_health_data(merged_df, collection)
