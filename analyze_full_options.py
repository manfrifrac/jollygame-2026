import json
import re
from collections import defaultdict

def extract_all_attributes(title):
    attr = {}
    
    # 1. Dimensions (e.g., 500x300, 3,60 m, Ø 350)
    dims = re.findall(r'(\d+(?:\.\d+)?\s*[xX*]\s*\d+(?:\.\d+)?|[oOØ\s]*\d+)', title)
    if dims: attr["Misura"] = dims[0].strip()
    
    # 2. Thickness (e.g., 40/100, 75/100, 400 micron)
    thick = re.findall(r'(\d+/\d+|\d+\s*micron)', title, re.IGNORECASE)
    if thick: attr["Spessore"] = thick[0].strip()
    
    # 3. Weight/Volume (e.g., 1kg, 5l, 500g)
    weight = re.findall(r'(\d+(?:\.\d+)?\s*(?:kg|l|g|gr|ml))', title, re.IGNORECASE)
    if weight: attr["Formato"] = weight[0].strip()
    
    # 4. Technical (e.g., 1CV, 6m3/h, 16W)
    tech = re.findall(r'(\d+(?:\.\d+)?\s*(?:CV|m³/h|W|V|Lumen))', title, re.IGNORECASE)
    if tech: attr["Dati Tecnici"] = tech[0].strip()
    
    # 5. Color/Finish
    colors = ['BLU', 'BEIGE', 'GRIGIO', 'ANTRACITE', 'LEGNO', 'PIETRA', 'GRAFITE', 'NORDIC', 'BIANCA', 'WPC', 'Marrone', 'Multicolor']
    for c in colors:
        if c.upper() in title.upper():
            attr["Colore / Finitura"] = c
            break

    # 6. Compatibility (e.g. for model Braga, Mint, etc.)
    models = ['MINT', 'BRAGA', 'EVORA', 'PAPAYA', 'MARBELLA', 'CARRA', 'LEMON', 'CITY', 'ORANGE', 'VERMELA', 'AVOCADO', 'SAFRAN', 'CANNELLE', 'GRENADE', 'MACADAMIA', 'BAMBU', 'VIOLETTE', 'VASTO', 'VANILLE', 'LILI', 'ATLANTIS', 'BORA BORA', 'FIDJI', 'MAURITIUS', 'PACIFIC', 'SICILIA', 'ISLANDA', 'KEA', 'KEOPS', 'MAGNOLIA', 'AMAZONIA']
    for m in models:
        if m.upper() in title.upper():
            attr["Modello Compatibile"] = m
            break

    return attr

def main():
    with open('listino_master_map.json', 'r', encoding='utf-8') as f:
        listino = json.load(f)
    
    # Re-grouping
    groups = defaultdict(list)
    for sku, info in listino.items():
        t = info['title'].upper().replace('KIT ', '').replace('PISCINA ', '').replace('PER ', '').replace('IN ', '').replace('COP.', '').replace('COPERTURA ', '')
        name = t.split()[0]
        group_key = f"{info['subcategory']} | {name}"
        groups[group_key].append((sku, info))

    final_plan = {}
    
    for g_name, items in groups.items():
        # Analyze which attributes actually vary in this specific group
        all_attrs = []
        for sku, info in items:
            all_attrs.append(extract_all_attributes(info['title']))
            
        # Find which keys have more than one unique value
        possible_keys = set()
        for a in all_attrs: possible_keys.update(a.keys())
        
        varying_keys = []
        for k in possible_keys:
            unique_vals = set(a.get(k) for a in all_attrs if a.get(k))
            if len(unique_vals) > 1:
                varying_keys.append(k)
        
        # Limit to 3 options (Shopify limit)
        varying_keys = sorted(varying_keys)[:3]
        
        # If no attributes vary but there are multiple items, use "Modello / Variante"
        if not varying_keys and len(items) > 1:
            varying_keys = ["Modello o Misura"]

        # Final variant mapping for this product
        variants = []
        for i, (sku, info) in enumerate(items):
            v_options = []
            current_attr = all_attrs[i]
            
            for k in varying_keys:
                val = current_attr.get(k) or "Standard"
                v_options.append({"name": val, "optionName": k})
            
            # If still no options (single product), Shopify needs at least one if we use productSet for variants
            if not v_options:
                v_options.append({"name": "Default", "optionName": "Tipologia"})

            variants.append({
                "sku": sku,
                "ean": info['ean'],
                "price": info['price'],
                "options": v_options,
                "title": info['title']
            })
            
        final_plan[g_name] = {
            "subcategory": items[0][1]['subcategory'],
            "option_names": varying_keys if varying_keys else ["Tipologia"],
            "variants": variants
        }

    with open('gre_multi_option_plan.json', 'w', encoding='utf-8') as f:
        json.dump(final_plan, f, indent=4)
    
    print(f"Creato piano multi-opzione per {len(final_plan)} gruppi prodotto.")

if __name__ == "__main__":
    main()
