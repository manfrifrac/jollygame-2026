import pandas as pd
import os

print("--- ZODIAC ---")
csv_zodiac = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\zodiac_enriched_data.csv"
if os.path.exists(csv_zodiac):
    df_z = pd.read_csv(csv_zodiac)
    for i, row in df_z.head(5).iterrows():
        print(f"[{row['Titolo']}] -> {row['Immagini']}")

print("\n--- LAGHETTO ---")
csv_laghetto = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\laghetto_full_export_enriched.csv"
if os.path.exists(csv_laghetto):
    df_l = pd.read_csv(csv_laghetto)
    for i, row in df_l.head(5).iterrows():
        print(f"[{row['Titolo']}] -> {row['Immagini']}")
