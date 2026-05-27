import pandas as pd
import json
import os

def prepare_ean_map():
    listino_path = "../../LISTINOMANUFACTURASGRE2026.xlsx"
    if not os.path.exists(listino_path):
        print(f"File listino non trovato in {os.path.abspath(listino_path)}")
        return

    # Leggi il listino (header riga 3)
    df = pd.read_excel(listino_path, header=2)
    
    # Crea mappa SKU -> EAN pulito
    ean_map = {}
    for _, row in df.iterrows():
        sku = str(row['ARTICOLO']).strip().upper()
        ean = row['EAN']
        if pd.notna(sku) and pd.notna(ean):
            # Converti EAN da float scientifico a stringa intera
            try:
                ean_str = str(int(float(ean)))
                if len(ean_str) >= 12:
                    ean_map[sku] = ean_str
            except:
                continue

    with open("sku_to_ean_map.json", "w", encoding="utf-8") as f:
        json.dump(ean_map, f, indent=2)
    
    print(f"✅ Mappa EAN creata con {len(ean_map)} codici.")

if __name__ == "__main__":
    prepare_ean_map()
