import sqlite3
import os

dbs = {
    "fluidra": ("fluidra_catalog.db", "product_relations"),
    "intex": ("intex_catalog.db", "spare_parts"), # Intex spesso ha i ricambi in una tabella separata
    "bestway": ("bestway_catalog.db", "product_relations")
}

for brand, (path, table) in dbs.items():
    if os.path.exists(path):
        print(f"\n--- {brand.upper()} ({path}) ---")
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Schema tabella relazioni
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [c[1] for c in cursor.fetchall()]
        print(f"Tabella Relazioni '{table}': {cols}")
        
        # Schema tabella prodotti (per descrizioni e media)
        prod_table = "products" if brand != "bestway" else "bestway_products"
        cursor.execute(f"PRAGMA table_info({prod_table})")
        p_cols = [c[1] for c in cursor.fetchall()]
        print(f"Tabella Prodotti '{prod_table}': {p_cols}")
        
        conn.close()
