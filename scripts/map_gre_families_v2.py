import pandas as pd
import json

def map_excel_to_families_v2():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
    df['SKU'] = df['ARTICOLO'].astype(str).str.strip().str.upper()
    
    # Nuova Mappa che include la FORMA
    families = {}
    
    for _, row in df.iterrows():
        d = str(row['DESCRIZIONE']).lower()
        s = str(row['SKU']).upper()
        if pd.isna(row['PREZZO DI VENDITA CONSIGLIATO 2026']): continue
        
        # 1. Detect Series
        series = None
        if "nordic" in d:
            series = "Islanda (Omega)" if ("88" in s or "omega" in d) else "Greenland (Pali)"
        elif "antracite" in d or "grigio" in d:
            series = "Skyathos (Omega)" if ("88" in s or "omega" in d) else "Kea (Pali)"
        elif "legno" in d and "acciaio" in d:
            series = "Amazonia (Omega)" if ("88" in s or "omega" in d) else "Mauritius (Pali)"
        elif "bianca" in d and "acciaio" in d:
            series = "Atlantis (Omega)" if ("88" in s or "omega" in d or "atlantis" in d) else "Fidji (Pali)"
            
        if not series: continue

        # 2. Detect Shape
        shape = "Ovale" if "ovale" in d else "Tonda" if "tonda" in d or "ø" in d or "pr" in s[:5] else "Rettangolare"
        
        full_key = f"{shape} Serie {series}"
            
        if full_key not in families: families[full_key] = []
        
        # 3. Extract Dimension
        dim = "Standard"
        dim_match = row['DESCRIZIONE'].split('Dim:')
        if len(dim_match) > 1:
            dim = dim_match[1].split()[0].replace('/', '-')
        elif "730" in d: dim = "730x375"
        elif "610" in d: dim = "610x375"
        elif "500" in d: dim = "500x300"
        elif "550" in d: dim = "Ø 550"
        elif "460" in d: dim = "Ø 460"
        elif "350" in d: dim = "Ø 350"

        families[full_key].append({
            "sku": s,
            "dim": dim,
            "price": f"{row['PREZZO DI VENDITA CONSIGLIATO 2026'] * 1.03:.2f}",
            "description": row['DESCRIZIONE']
        })

    with open("gre_family_import_plan_v2.json", "w", encoding="utf-8") as f:
        json.dump(families, f, indent=2)
    
    print(f"✅ Nuovo piano creato con {len(families)} raggruppamenti (Serie + Forma).")
    for k, v in families.items():
        print(f" - {k}: {len(v)} varianti")

if __name__ == "__main__":
    map_excel_to_families_v2()
