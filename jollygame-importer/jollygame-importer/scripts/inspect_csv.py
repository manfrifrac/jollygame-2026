import pandas as pd
import os

csv_path = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\zodiac_enriched_data.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows (Titolo e Immagini):")
    print(df[['Titolo', 'Immagini']].head(5))
else:
    print("File not found")
