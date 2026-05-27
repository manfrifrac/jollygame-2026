import sqlite3
import os
import json

ROOT_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame'
DB_PATHS = {
    "Fluidra": os.path.join(ROOT_PATH, 'fluidra_clean.db'),
    "Bestway": os.path.join(ROOT_PATH, 'bestway_clean.db'),
    "Intex": os.path.join(ROOT_PATH, 'intex_clean.db')
}

for name, path in DB_PATHS.items():
    if not os.path.exists(path): continue
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    table = "products" if name != "Bestway" else "bestway_products"
    img_col = "images_json" if name == "Fluidra" else "images"
    
    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE is_spare_part = 1 AND {img_col} != '[]' AND {img_col} != '' AND {img_col} IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"[{name}] Ricambi con immagini: {count}")
    
    if count > 0:
        cursor.execute(f"SELECT sku, title, {img_col} FROM {table} WHERE is_spare_part = 1 AND {img_col} != '[]' AND {img_col} != '' LIMIT 3")
        examples = cursor.fetchall()
        for e in examples:
            print(f"  - {e[0]}: {e[1]} -> {e[2]}")
    conn.close()
