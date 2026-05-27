import pandas as pd
import re
from collections import defaultdict

def get_attributes(title):
    res = {}
    # Dimensions: 500x300, Ø 350
    dim_match = re.search(r'(\d+\s*[xX]\s*\d+|[oOØ\s]*\d+)', title)
    if dim_match: res['Misura'] = dim_match.group(1).strip()
    
    # Thickness
    thick_match = re.search(r'(\d+/\d+|\d+\s*micron)', title)
    if thick_match: res['Spessore'] = thick_match.group(1).strip()
    
    # Color
    for c in ['BLU', 'BEIGE', 'GRIGIO', 'ANTRACITE', 'LEGNO', 'PIETRA', 'GRAFITE', 'NORDIC', 'BIANCA', 'WPC', 'MOSAICATO']:
        if c in title.upper():
            res['Colore'] = c.capitalize()
            break
            
    # System
    for s in ['BEADED', 'OVERLAP', 'OMEGA', 'RINFORZI']:
        if s in title.upper():
            res['Sistema'] = s.capitalize()
            break
            
    return res

def get_base_name(title, attrs):
    t = title
    for val in attrs.values():
        t = t.replace(val, '')
    
    t = re.sub(r'[hH]\s*\d+', '', t)
    t = t.upper().replace('KIT ', '').replace('PISCINA ', '').replace('PER ', '').replace('IN ', '').replace('COP.', '').replace('COPERTURA ', '')
    t = re.sub(r'\d+(?:\.\d+)?\s*(?:kg|l|g|gr|ml|m|m3/h|W|V|Lumen)', '', t, flags=re.IGNORECASE)
    
    words = [w for w in t.split() if len(w) > 2]
    return ' '.join(words[:4]).strip(',- ')

def main():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx')
    groups = defaultdict(list)
    
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper()
        if sku and sku not in ['NAN', 'REF', 'ARTICOLO'] and len(sku) > 2:
            attrs = get_attributes(row.iloc[7])
            base = get_base_name(row.iloc[7], attrs)
            
            # To have FEWER variants, we put Color and System into the Product Name
            # Example: "Liner Blu Beaded" -> Variants are only Sizes
            prod_name = base
            if 'Colore' in attrs: prod_name += f" {attrs['Colore']}"
            if 'Sistema' in attrs: prod_name += f" {attrs['Sistema']}"
            
            groups[prod_name].append((sku, attrs))

    print(f"Totale Prodotti distinti: {len(groups)}")
    
    print("\n--- ESEMPI DI SUDDIVISIONE VARIANTI ---")
    for name in sorted(groups.keys()):
        skus = groups[name]
        if len(skus) > 1:
            # Find which attributes actually vary
            v_keys = []
            for k in ['Misura', 'Spessore']: # These are the only ones left as variants
                unique_vals = set(a.get(k) for s, a in skus if a.get(k))
                if len(unique_vals) > 1:
                    v_keys.append(k)
            
            if not v_keys: v_keys = ["Modello"]
            
            print(f"PRODOTTO: Gre - {name}")
            print(f"   * Opzioni Selettore: {v_keys}")
            print(f"   * Numero Varianti: {len(skus)}")
            print(f"   * Esempi SKU: {[s for s, a in skus[:3]]}")
            print("-" * 30)

if __name__ == "__main__":
    main()
