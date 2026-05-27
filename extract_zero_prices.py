import sqlite3
import os
import json

def audit_publishable():
    results = []
    dbs = [
        ("fluidra_clean.db", "products", "Fluidra", "price_list"),
        ("intex_clean.db", "products", "Intex", "price"),
        ("bestway_clean.db", "bestway_products", "Bestway", "price")
    ]

    for db_path, table, brand, p_col in dbs:
        if not os.path.exists(db_path): continue
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prodotti con Prezzo > 0
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {p_col} > 0 AND is_spare_part = 0")
        with_price = cursor.fetchone()[0]
        
        # Prodotti con Prezzo = 0
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE ({p_col} IS NULL OR {p_col} = 0) AND is_spare_part = 0")
        zero_price = cursor.fetchone()[0]
        
        # Vediamo quali categorie perdiamo (i top 5 raggruppamenti con prezzo 0)
        cat_col = 'taxonomy' if brand == 'Fluidra' else ('categories' if brand == 'Intex' else 'category')
        cursor.execute(f"SELECT {cat_col}, COUNT(*) as c FROM {table} WHERE ({p_col} IS NULL OR {p_col} = 0) AND is_spare_part = 0 GROUP BY {cat_col} ORDER BY c DESC LIMIT 5")
        lost_cats = cursor.fetchall()

        results.append({
            "Brand": brand,
            "Pronti (Prezzo > 0)": with_price,
            "Esclusi (Prezzo 0)": zero_price,
            "Cosa perdiamo (Esempi)": [f"{r[0]} ({r[1]})" for r in lost_cats]
        })
        conn.close()
    
    return results

print(json.dumps(audit_publishable(), indent=2))
