import sqlite3
import os

db_path = 'fluidra_clean.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM products WHERE (taxonomy LIKE '%Gre%' OR title LIKE '%Gre%') AND (description IS NOT NULL AND description != '')")
    with_desc = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM products WHERE (taxonomy LIKE '%Gre%' OR title LIKE '%Gre%') AND (images_json IS NOT NULL AND images_json != '[]')")
    with_images = cursor.fetchone()[0]
    print(f"Gre products in Fluidra DB with description: {with_desc}")
    print(f"Gre products in Fluidra DB with images: {with_images}")
    conn.close()
else:
    print("DB not found")
