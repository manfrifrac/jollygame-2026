import sqlite3
import json
import os

def update_intex_categories():
    db_path = "intex_clean.db"
    map_path = "intex_url_category_map.json"
    
    if not os.path.exists(db_path) or not os.path.exists(map_path):
        print("File mancanti.")
        return

    with open(map_path, "r", encoding="utf-8") as f:
        cat_to_urls = json.load(f)

    # Invert mapping: URL -> List of Categories
    url_to_cats = {}
    for cat, urls in cat_to_urls.items():
        for url in urls:
            if url not in url_to_cats:
                url_to_cats[url] = []
            url_to_cats[url].append(cat)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updates = 0
    for url, cats in url_to_cats.items():
        # Join categories with ' > ' to represent hierarchy if possible, 
        # but here they might just be multiple labels.
        # Let's pick the most specific one (usually the last in the URL path or the longest name)
        # or just join them.
        cat_string = " | ".join(sorted(list(set(cats))))
        
        # Match URL (handle trailing slashes and common differences)
        cursor.execute("UPDATE products SET categories = ? WHERE url = ? OR url = ?", (cat_string, url, url + "/"))
        updates += cursor.rowcount

    conn.commit()
    conn.close()
    print(f"Aggiornamento completato. {updates} prodotti Intex categorizzati.")

if __name__ == "__main__":
    update_intex_categories()
