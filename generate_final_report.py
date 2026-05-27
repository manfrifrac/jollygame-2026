import pandas as pd
import re
import json
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
        t = t.replace(val, '').replace(val.upper(), '').replace(val.capitalize(), '')
    
    t = re.sub(r'[hH]\s*\d+', '', t)
    t = t.upper().replace('KIT ', '').replace('PISCINA ', '').replace('PER ', '').replace('IN ', '').replace('COP.', '').replace('COPERTURA ', '')
    t = re.sub(r'\d+(?:\.\d+)?\s*(?:kg|l|g|gr|ml|m|m3/h|W|V|Lumen)', '', t, flags=re.IGNORECASE)
    
    words = [w for w in t.split() if len(w) > 2]
    return ' '.join(words[:5]).strip(',- ')

def main():
    with open('listino_master_map.json', 'r', encoding='utf-8') as f:
        listino = json.load(f)
        
    groups = defaultdict(list)
    
    for sku, info in listino.items():
        title = info['title']
        attrs = get_attributes(title)
        base = get_base_name(title, attrs)
        
        # Product Title Logic
        prod_name = base
        if 'Colore' in attrs: prod_name += f" {attrs['Colore']}"
        if 'Sistema' in attrs: prod_name += f" {attrs['Sistema']}"
        
        groups[prod_name].append({
            "sku": sku,
            "ean": info['ean'],
            "original_title": title,
            "parent_category": info['category'],
            "subcategory": info['subcategory'],
            "price": info['price'],
            "attrs": attrs
        })

    report_rows = []
    
    for prod_name, variants in groups.items():
        # Determine which attributes vary to name the options
        v_keys = []
        for k in ['Misura', 'Spessore']:
            unique_vals = set(v['attrs'].get(k) for v in variants if v['attrs'].get(k))
            if len(unique_vals) > 1:
                v_keys.append(k)
        
        # If no standard varying keys but multiple variants, use 'Dettaglio'
        if not v_keys and len(variants) > 1:
            v_keys = ["Dettaglio"]

        for v in variants:
            row = {
                "Prodotto_Shopify": f"Gre - {prod_name}",
                "Categoria_Padre": v['parent_category'],
                "Sottocategoria": v['subcategory'],
                "SKU": v['sku'],
                "EAN": v['ean'],
                "Prezzo_2026": v['price'],
                "Titolo_Originale_Listino": v['original_title']
            }
            
            # Fill options
            for idx, opt_name in enumerate(v_keys):
                val = v['attrs'].get(opt_name)
                if not val and opt_name == "Dettaglio":
                    val = v['original_title'][-30:] 
                row[f"Opzione_{idx+1}_Nome"] = opt_name
                row[f"Opzione_{idx+1}_Valore"] = val or "Standard"
                
            report_rows.append(row)

    df_report = pd.DataFrame(report_rows)
    # Reorder columns for clarity
    cols = ["Prodotto_Shopify", "Categoria_Padre", "Sottocategoria", "SKU", "EAN", "Prezzo_2026", 
            "Opzione_1_Nome", "Opzione_1_Valore", "Opzione_2_Nome", "Opzione_2_Valore", 
            "Titolo_Originale_Listino"]
    df_report = df_report[[c for c in cols if c in df_report.columns]]
    
    df_report.to_csv('REPORT_STRUTTURA_PRODOTTI_GRE.csv', index=False, encoding='utf-8-sig')
    print(f"Report generato con successo: REPORT_STRUTTURA_PRODOTTI_GRE.csv ({len(df_report)} righe)")

if __name__ == "__main__":
    main()
