import pandas as pd
import json

def map_excel_to_families():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
    df['SKU'] = df['ARTICOLO'].astype(str).str.strip().str.upper()
    
    families = {
        "Islanda (Nordic Omega)": [],
        "Greenland (Nordic Pali)": [],
        "Skyathos (Antracite Omega)": [],
        "Kea (Antracite Pali)": [],
        "Amazonia (Legno Omega)": [],
        "Mauritius (Legno Pali)": [],
        "Atlantis (Bianca Omega)": [],
        "Fidji (Bianca Pali)": []
    }
    
    for _, row in df.iterrows():
        d = str(row['DESCRIZIONE']).lower()
        s = str(row['SKU']).upper()
        if pd.isna(row['PREZZO DI VENDITA CONSIGLIATO 2026']): continue
        
        # Classification
        target = None
        if "nordic" in d:
            target = "Islanda (Nordic Omega)" if ("88" in s or "omega" in d) else "Greenland (Nordic Pali)"
        elif "antracite" in d or "grigio" in d:
            target = "Skyathos (Antracite Omega)" if ("88" in s or "omega" in d) else "Kea (Antracite Pali)"
        elif "legno" in d and "acciaio" in d:
            target = "Amazonia (Legno Omega)" if ("88" in s or "omega" in d) else "Mauritius (Legno Pali)"
        elif "bianca" in d and "acciaio" in d:
            target = "Atlantis (Bianca Omega)" if ("88" in s or "omega" in d or "atlantis" in d) else "Fidji (Bianca Pali)"
            
        if target:
            # Extract dimension
            dim = "Standard"
            dim_match = row['DESCRIZIONE'].split('Dim:')
            if len(dim_match) > 1:
                dim = dim_match[1].split()[0]
            elif "730" in d: dim = "730x375"
            elif "610" in d: dim = "610x375"
            elif "500" in d: dim = "500x300"
            
            families[target].append({
                "sku": s,
                "dim": dim,
                "price": f"{row['PREZZO DI VENDITA CONSIGLIATO 2026'] * 1.03:.2f}",
                "description": row['DESCRIZIONE']
            })

    # Filter out empty families
    families = {k: v for k, v in families.items() if len(v) > 0}
    
    with open("gre_family_import_plan.json", "w", encoding="utf-8") as f:
        json.dump(families, f, indent=2)
    
    print(f"✅ Piano di importazione creato per {len(families)} famiglie.")
    for k, v in families.items():
        print(f" - {k}: {len(v)} varianti")

if __name__ == "__main__":
    map_excel_to_families()
