import pandas as pd
import json

def map_excel_to_kits_only():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
    df['SKU'] = df['ARTICOLO'].astype(str).str.strip().str.upper()
    
    # FILTRO SOLO I KIT COMPLETI
    # In Gre i kit iniziano quasi sempre con KIT, KPCO, o KPE
    df_kits = df[df['SKU'].str.startswith(('KIT', 'KPCO', 'KPE'), na=False)]
    
    families = {}
    
    for _, row in df_kits.iterrows():
        d = str(row['DESCRIZIONE']).lower()
        s = str(row['SKU']).upper()
        if pd.isna(row['PREZZO DI VENDITA CONSIGLIATO 2026']): continue
        
        # Detect Series
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

        # Detect Shape
        shape = "Ovale" if "ovale" in d else "Tonda" if "tonda" in d or "ø" in d else "Rettangolare"
        
        full_key = f"{shape} Serie {series}"
        if full_key not in families: families[full_key] = []
        
        # Dimension
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

    with open("gre_kits_only_plan.json", "w", encoding="utf-8") as f:
        json.dump(families, f, indent=2)
    
    print(f"✅ Piano KITS creato con {len(families)} raggruppamenti.")
    for k, v in families.items():
        print(f" - {k}: {len(v)} misure reali")

if __name__ == "__main__":
    map_excel_to_kits_only()
