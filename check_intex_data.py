import sqlite3
import json
import os

def investigate_missing():
    db_path = "intex_clean.db"
    map_path = "intex_url_category_map.json"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get missing
    cursor.execute("SELECT url, title, sku FROM products WHERE categories IS NULL OR categories = '' OR categories = '[]'")
    missing = cursor.fetchall()
    print(f"Totale prodotti senza categoria nel DB: {len(missing)}")
    
    # Load the map we generated
    with open(map_path, "r", encoding="utf-8") as f:
        cat_map = json.load(f)
    
    all_mapped_urls = set()
    for urls in cat_map.values():
        for u in urls:
            all_mapped_urls.add(u.rstrip('/'))
            
    print(f"Totale URL mappati nel JSON: {len(all_mapped_urls)}")
    
    print("\n--- ESEMPI DI PRODOTTI MANCANTI ---")
    found_in_map_but_not_db = 0
    for url, title, sku in missing[:20]:
        clean_url = url.rstrip('/')
        in_map = clean_url in all_mapped_urls
        if in_map: found_in_map_but_not_db += 1
        print(f"SKU: {sku} | In Map: {in_map} | URL: {url}")

    conn.close()

if __name__ == "__main__":
    investigate_missing()
