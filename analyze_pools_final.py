import json
import re
from collections import defaultdict

def extract_pool_series(title):
    # Priorities series names found in Gre catalog
    series = [
        'SUNBAY', 'LEMON', 'MINT', 'BRAGA', 'EVORA', 'PAPAYA', 'MARBELLA', 'CARRA', 'CITY', 'ORANGE', 'VERMELA', 
        'AVOCADO', 'SAFRAN', 'CANNELLE', 'GRENADE', 'MACADAMIA', 'BAMBU', 'VIOLETTE', 'VASTO', 'VANILLE', 'LILI',
        'ATLANTIS', 'BORA BORA', 'FIDJI', 'MAURITIUS', 'PACIFIC', 'SICILIA', 'ISLANDA', 'KEA', 'KEOPS', 'MAGNOLIA', 'AMAZONIA',
        'AVANTGARDE', 'TERRAPOOLS', 'NORDIC'
    ]
    for s in series:
        if s in title.upper():
            return s
    # If no specific series, group by decoration/type
    if 'NORDIC' in title.upper(): return 'NORDIC SERIES'
    if 'ANTRACITE' in title.upper(): return 'ANTRACITE SERIES'
    if 'BIANCA' in title.upper(): return 'WHITE SERIES'
    if 'LEGNO' in title.upper(): return 'WOOD SERIES'
    if 'COMPOSITO' in title.upper(): return 'COMPOSITE SERIES'
    
    return "ALTRE PISCINE GRE"

def extract_pool_attributes(title):
    attr = {}
    
    # 1. Dimensions
    dims = re.findall(r'(\d+\s*[xX]\s*\d+|[oOØ\s]*\d+)', title)
    if dims: attr["Misura"] = dims[0].strip()
    
    # 2. Height
    h = re.findall(r'[hH]\s*(\d+)', title)
    if h: attr["Altezza"] = f"{h[0]} cm"
    
    # 3. Support System
    if 'OMEGA' in title.upper():
        attr["Supporto"] = "Sistema Omega (senza gambe)"
    elif 'RINFORZI' in title.upper():
        r = re.search(r'(\d+)\s+RINFORZI', title.upper())
        attr["Supporto"] = f"Rinforzi laterali ({r.group(1)} per lato)" if r else "Rinforzi laterali"
    else:
        attr["Supporto"] = "Standard"

    # 4. Decoration (only if not already in series)
    decors = ['NORDIC', 'ANTRACITE', 'LEGNO', 'BIANCA', 'PIETRA', 'GRAFITE']
    for d in decors:
        if d in title.upper():
            attr["Finitura"] = d.capitalize()
            break
            
    # 5. Technical (Filtro e Liner)
    filtro = re.search(r'FILTRO A (SABBIA|CARTUCCIA|AQUALOON) DA (\d+m³/h|\d+)', title.upper())
    if filtro:
        attr["Filtrazione"] = f"{filtro.group(1)} {filtro.group(2)}"
        
    liner = re.search(r'LINER (.*?) (\d+/\d+)', title.upper())
    if liner:
        attr["Liner"] = f"{liner.group(1)} {liner.group(2)}"

    return attr

def main():
    with open('listino_master_map.json', 'r', encoding='utf-8') as f:
        listino = json.load(f)
    
    pool_groups = defaultdict(list)
    for sku, info in listino.items():
        if info['subcategory'] == 'Piscine in acciaio' or info['subcategory'] == 'Piscine in legno' or info['subcategory'] == 'Piscine in composite':
            series = extract_pool_series(info['title'])
            pool_groups[series].append((sku, info))

    print(f"Rilevate {len(pool_groups)} Serie di Piscine Gre.\n")
    
    final_pool_plan = {}
    for series, items in pool_groups.items():
        print(f"SERIE: {series} ({len(items)} modelli)")
        
        variants = []
        for sku, info in items:
            attrs = extract_pool_attributes(info['title'])
            
            # Create a combined option string for Shopify (max 3 options)
            # We'll use: 1. Misura/Altezza, 2. Supporto, 3. Finitura (if relevant)
            v_options = [
                {"name": f"{attrs.get('Misura', 'Unica')} x {attrs.get('Altezza', 'Std')}", "optionName": "Dimensioni"},
                {"name": attrs.get('Supporto', 'Standard'), "optionName": "Struttura"},
                {"name": attrs.get('Finitura', 'Original'), "optionName": "Finitura"}
            ]
            
            variants.append({
                "sku": sku,
                "ean": info['ean'],
                "price": info['price'],
                "options": v_options,
                "tech_details": {
                    "Filtrazione": attrs.get("Filtrazione", "Inclusa"),
                    "Liner": attrs.get("Liner", "Incluso")
                }
            })
        
        final_pool_plan[series] = {
            "title": f"Piscine Gre Serie {series.capitalize()}",
            "category": items[0][1]['subcategory'],
            "variants": variants
        }

    with open('gre_pools_deep_plan.json', 'w', encoding='utf-8') as f:
        json.dump(final_pool_plan, f, indent=4)
    print("\nAnalisi profonda piscine completata: gre_pools_deep_plan.json")

if __name__ == "__main__":
    main()
