import sqlite3
import json
import os
import re

def update_by_sku():
    db_path = "intex_clean.db"
    map_path = "intex_url_category_map_v2.json"
    
    with open(map_path, "r", encoding="utf-8") as f:
        cat_map = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updates = 0
    
    # Prepariamo una regex per estrarre lo SKU dall'URL (es: 26378NP)
    sku_pattern = re.compile(r'(\d{5}(?:np|))', re.IGNORECASE)

    for cat, urls in cat_map.items():
        for url in urls:
            match = sku_pattern.search(url)
            if match:
                sku_found = match.group(1).upper()
                # Proviamo ad aggiornare per SKU
                cursor.execute("UPDATE products SET categories = ? WHERE sku LIKE ?", (cat, f"%{sku_found}%"))
                updates += cursor.rowcount
            
            # Proviamo anche il match per URL parziale (slug finale)
            slug = url.rstrip('/').split('/')[-1]
            cursor.execute("UPDATE products SET categories = ? WHERE url LIKE ?", (cat, f"%{slug}%"))
            updates += cursor.rowcount

    conn.commit()
    conn.close()
    print(f"Aggiornamento completato via SKU/Slug. {updates} record toccati.")

if __name__ == "__main__":
    update_by_sku()
