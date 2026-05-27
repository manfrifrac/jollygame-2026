import pandas as pd
import json

def analyze_gre_series():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
    
    def classify(row):
        d = str(row['DESCRIZIONE']).lower()
        sku = str(row['ARTICOLO']).upper()
        
        # Detect Shape
        shape = "OVALE" if "ovale" in d else "TONDA" if "tonda" in d else "RETTANGOLARE" if "rettangolare" in d else "QUADRATA" if "quadrata" in d else "ALTRO"
        
        # Detect Decor
        decor = "NORDIC" if "nordic" in d else "ANTRACITE" if "grigio antracite" in d else "LEGNO" if "legno" in d else "BIANCA" if "bianca" in d else "COMPOSITO" if "composito" in d else "ACCIAIO"
        
        # Detect System
        system = "OMEGA (Senza Pali)" if ("88" in sku or "sistema omega" in d) else "PALI (Contrafforti)" if ("rinforzi laterali" in d or "pali" in d) else "STANDARD"
        
        # Assign Commercial Name (Gre Logic)
        name = "Sconosciuta"
        if decor == "NORDIC":
            if shape == "OVALE":
                name = "ISLANDA" if system == "OMEGA (Senza Pali)" else "GREENLAND"
            else:
                name = "NORDIC TONDA"
        elif decor == "ANTRACITE":
            if shape == "OVALE":
                name = "SKYATHOS" if system == "OMEGA (Senza Pali)" else "KEA"
            else:
                name = "IRAKLION (Tonda)"
        elif decor == "LEGNO":
            if shape == "OVALE":
                name = "AMAZONIA" if system == "OMEGA (Senza Pali)" else "MAURITIUS"
            elif shape == "TONDA":
                name = "PACIFIC (Tonda)"
            else:
                name = "PISCINA LEGNO VERO"
        elif decor == "BIANCA":
            if shape == "OVALE":
                name = "ATLANTIS" if system == "OMEGA (Senza Pali)" else "FIDJI"
            else:
                name = "BORA BORA (Tonda)"
                
        return pd.Series([name, shape, system, decor])

    df[['SERIE_NAME', 'FORMA', 'SISTEMA', 'DECORO']] = df.apply(classify, axis=1)
    
    # Filtra solo le piscine (Categorie che contengono piscine)
    piscine = df[df['CATEGORIA 3'].str.contains('Piscine', na=False, case=False)]
    
    # Raggruppa per Serie e Decoro per vedere come dovrebbero essere accorpate
    summary = piscine.groupby(['SERIE_NAME', 'DECORO', 'SISTEMA']).size().reset_index(name='Num_Misure')
    
    print("📊 ANALISI STRUTTURALE SERIE GRE:")
    print(summary.to_string())
    
    # Salva il mapping per l'importazione
    piscine[['ARTICOLO', 'DESCRIZIONE', 'SERIE_NAME', 'FORMA', 'SISTEMA']].to_json('gre_series_mapping.json', orient='records', indent=2)

if __name__ == "__main__":
    analyze_gre_series()
