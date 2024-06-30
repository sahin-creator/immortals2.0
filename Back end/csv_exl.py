import pandas as pd

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

blood_details = './patient_details/Blood_details.csv'
blood_pressure = './patient_details/Blood_pressure.csv'
blood_sugar = './patient_details/Blood_suger.csv'  # Corrected variable name
height = './patient_details/Height.csv'
spo2 = './patient_details/spo2.csv'
weight = './patient_details/Weight.csv'

bd_df = read_csv_with_exception(blood_details)
bp_df = read_csv_with_exception(blood_pressure)
bs_df = read_csv_with_exception(blood_sugar)
ht_df = read_csv_with_exception(height)
sp_df = read_csv_with_exception(spo2)
wg_df = read_csv_with_exception(weight)

# Check if any of the DataFrames is None before proceeding
if any(df is None for df in (bd_df, bp_df, bs_df, ht_df, sp_df, wg_df)):
    print("Error: One or more CSV files failed to load. Please check the file paths.")
else:
    bd_df = bd_df[[0]]
    bp_df = bp_df[[0]]
    bs_df = bs_df[[0]]
    ht_df = ht_df[[0]]
    sp_df = sp_df[[0]]
    wg_df = wg_df[[0]]

    d1 = bd_df[0].str.split('_')
    d2 = bp_df[0].str.split('_')
    d3 = bs_df[0].str.split('_')
    d4 = ht_df[0].str.split('_')
    d5 = sp_df[0].str.split('_')
    d6 = wg_df[0].str.split('_')

    d1 = pd.DataFrame(list(d1.values), columns=['name', 'date', 'time', 'place', 'blood group'])
    d2 = pd.DataFrame(list(d2.values), columns=['name', 'date', 'time', 'place', 'blood pressure'])
    d3 = pd.DataFrame(list(d3.values), columns=['name', 'date', 'time', 'place', 'sugar level'])  # Corrected column name
    d4 = pd.DataFrame(list(d4.values), columns=['name', 'date', 'time', 'place', 'height'])
    d5 = pd.DataFrame(list(d5.values), columns=['name', 'date', 'time', 'place', 'spo2'])
    d6 = pd.DataFrame(list(d6.values), columns=['name', 'date', 'time', 'place', 'weight'])

    pk_columns = ['name', 'date', 'time', 'place']

    temp1 = pd.merge(d1, d2, on=pk_columns)
    temp2 = pd.merge(d3, d4, on=pk_columns)
    temp3 = pd.merge(d5, d6, on=pk_columns)

    temp4 = pd.merge(temp1, temp2, on=pk_columns)

    df = pd.merge(temp4, temp3, on=pk_columns)

    df.head(10)

    try:
        df.to_excel('output.xlsx',index=False)
        print("Output successfully saved to 'output.xlsx'")
    except Exception as e:
        print(f"An error occurred while saving the output to Excel: {e}")
