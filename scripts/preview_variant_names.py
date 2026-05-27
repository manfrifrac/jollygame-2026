import pandas as pd
import json

def preview_variant_names():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
    df['SKU'] = df['ARTICOLO'].astype(str).str.strip().str.upper()
    
    preview = []
    for _, row in df.head(100).iterrows():
        sku = row['SKU']
        desc = str(row['DESCRIZIONE'])
        
        if pd.isna(row['PREZZO DI VENDITA CONSIGLIATO 2026']): continue
        if not sku.startswith(('KIT', 'KPCO', 'KPE')): continue

        # Estrazione Dimensione
        dim = "Standard"
        if "Dim:" in desc:
            dim = desc.split("Dim:")[1].split("h")[0].strip().replace("Est:", "").strip()
        elif "ø" in desc.lower():
            dim = "Ø " + desc.lower().split("ø")[1].split()[0].strip()
        
        # Estrazione Filtro
        filtro = ""
        if "sabbia" in desc.lower(): filtro = "Sabbia"
        elif "cartuccia" in desc.lower(): filtro = "Cartuccia"
        elif "aqualoon" in desc.lower(): filtro = "Aqualoon"
        
        # Estrazione Sistema Omega
        sistema = ""
        if "omega" in desc.lower(): sistema = "Omega (No Pali)"
        
        clean_name = f"{dim}"
        details = []
        if filtro: details.append(f"Filtro {filtro}")
        if sistema: details.append(sistema)
        
        if details:
            clean_name += " - " + " / ".join(details)
            
        preview.append({
            "sku": sku,
            "original": desc[:50] + "...",
            "proposed_name": clean_name
        })

    print(json.dumps(preview[:15], indent=2))

if __name__ == "__main__":
    preview_variant_names()
