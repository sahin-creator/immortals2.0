import pandas as pd

# Input text file path
text_file_path = 'F:\patient_data\Weight\Weight.txt'

# Output CSV file path
csv_file_path = 'Weight.csv'

# Read the text file into a DataFrame using pandas
df = pd.read_csv(text_file_path, sep='\t')  # Assuming tab-separated values

# Write the DataFrame to a CSV file
df.to_csv(csv_file_path, index=False)

print(f"Conversion from {text_file_path} to {csv_file_path} complete.")
