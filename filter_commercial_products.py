import sqlite3
import json
import os

def create_unified_taxonomy(db_path, table_name, brand):
    if not os.path.exists(db_path): return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cat_col = 'taxonomy' if brand == 'Fluidra' else ('categories' if brand == 'Intex' else 'category')
    
    cursor.execute(f"SELECT * FROM {table_name} WHERE is_spare_part = 0")
    prods = [dict(r) for r in cursor.fetchall()]
    
    unified_data = []
    for p in prods:
        p['brand'] = brand # Aggiungo il brand mancante
        raw_cat = str(p.get(cat_col, '')).lower()
        title = str(p.get('title', '')).lower()
        
        jolly_cat = "Accessori e Manutenzione"
        if any(x in raw_cat for x in ["piscine", "piscina", "pool"]) or any(x in title for x in ["piscina", "pool"]):
            if "acciaio" in raw_cat or "acciaio" in title: jolly_cat = "Piscine > Acciaio"
            elif "legno" in raw_cat or "legno" in title: jolly_cat = "Piscine > Legno"
            elif "gonfiabili" in raw_cat or "easy set" in title: jolly_cat = "Piscine > Gonfiabili"
            else: jolly_cat = "Piscine > Frame"
        elif any(x in raw_cat for x in ["pulitori", "robot", "pulizia"]) or any(x in title for x in ["robot", "pulitore"]):
            jolly_cat = "Pulizia e Robot"
        elif any(x in raw_cat for x in ["pompe", "filtri", "filtrazione", "pump"]) or any(x in title for x in ["pompa", "filtro"]):
            jolly_cat = "Filtrazione e Pompe"
        elif any(x in raw_cat for x in ["spa", "idromassaggio", "purespa"]):
            jolly_cat = "Spa e Benessere"

        has_img = p.get('images_json') or p.get('images') or p.get('image_url')
        if has_img and len(title) > 10:
            p['jolly_taxonomy'] = jolly_cat
            unified_data.append(p)
            
    conn.close()
    return unified_data

f = create_unified_taxonomy("fluidra_clean.db", "products", "Fluidra")
i = create_unified_taxonomy("intex_clean.db", "products", "Intex")
b = create_unified_taxonomy("bestway_clean.db", "bestway_products", "Bestway")

all_top = f + i + b
print(f"Totale prodotti filtrati (TOP): {len(all_top)}")

top_skus = [{"sku": p['sku'], "title": p['title'], "brand": p['brand']} for p in all_top]
with open("top_products_list.json", "w", encoding="utf-8") as f_out:
    json.dump(top_skus, f_out, indent=2)
