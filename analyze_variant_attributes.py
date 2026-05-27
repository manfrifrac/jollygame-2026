import json
import re
from collections import defaultdict

def extract_attributes(title):
    # Regex to find dimensions like 500x300 or Ø 350
    dims = re.findall(r'(\d+\s*[xX]\s*\d+|[oOØ\s]*\d+)', title)
    
    # Height often follows 'h'
    height = re.findall(r'[hH]\s*(\d+)', title)
    
    # Material/Finitura/Color (Gre common keywords)
    colors = ['BLU', 'BEIGE', 'GRIGIO', 'ANTRACITE', 'LEGNO', 'PIETRA', 'GRAFITE', 'NORDIC', 'BIANCA', 'WPC']
    found_colors = [c for c in colors if c in title.upper()]
    
    return {
        "dims": dims[0] if dims else None,
        "height": height[0] if height else None,
        "color": found_colors[0] if found_colors else None
    }

def main():
    with open('listino_master_map.json', 'r', encoding='utf-8') as f:
        listino = json.load(f)
    
    # Group by Subcategory + first meaningful word (Brand/Model)
    groups = defaultdict(list)
    for sku, info in listino.items():
        t = info['title'].upper().replace('KIT ', '').replace('PISCINA ', '').replace('PER ', '').replace('IN ', '').replace('COP.', '').replace('COPERTURA ', '')
        name = t.split()[0]
        group_key = f"{info['subcategory']} | {name}"
        groups[group_key].append(info)

    analysis = {}
    for g_name, items in groups.items():
        if len(items) <= 1: continue # Only analyze groups with variants
        
        # Check what changes between items in the same group
        changing_dims = len(set(extract_attributes(i['title'])['dims'] for i in items)) > 1
        changing_height = len(set(extract_attributes(i['title'])['height'] for i in items)) > 1
        changing_color = len(set(extract_attributes(i['title'])['color'] for i in items)) > 1
        
        options = []
        if changing_dims: options.append("Dimensioni")
        if changing_height: options.append("Altezza")
        if changing_color: options.append("Finitura / Colore")
        
        # If no standard change found, use a generic descriptive option
        if not options:
            options.append("Modello / Variante")
            
        analysis[g_name] = {
            "count": len(items),
            "suggested_options": options,
            "examples": [i['title'] for i in items[:3]]
        }

    print(json.dumps(analysis, indent=4))

if __name__ == "__main__":
    main()
