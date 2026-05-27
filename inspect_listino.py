import pandas as pd
import os

file_path = 'LISTINOMANUFACTURASGRE2026.xlsx'
if not os.path.exists(file_path):
    print(f"File {file_path} not found.")
else:
    try:
        # Just read the first few rows to see the structure
        df_full = pd.read_excel(file_path)
        print("\nRow 67:")
        print(df_full.iloc[67].values)
        
    except Exception as e:
        print(f"Error: {e}")
