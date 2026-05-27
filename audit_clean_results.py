import sqlite3
import os
import json

def audit_clean_db(db_path, table_name, brand):
    if not os.path.exists(db_path): return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Conteggio Totale
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total = cursor.fetchone()[0]
    
    # Conteggio Prodotti vs Ricambi
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE is_spare_part = 0")
    prods = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE is_spare_part = 1")
    spares = cursor.fetchone()[0]
    
    # Conteggio con EAN
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE ean IS NOT NULL AND ean != '' AND ean != 'N/A' AND ean != 'None'")
    with_ean = cursor.fetchone()[0]
    
    # Esempi di titoli normalizzati
    cursor.execute(f"SELECT title FROM {table_name} WHERE is_spare_part = 0 LIMIT 5")
    samples = [r['title'] for r in cursor.fetchall()]
    
    conn.close()
    return {
        "brand": brand,
        "totale": total,
        "prodotti_finiti": prods,
        "ricambi_tecnici": spares,
        "copertura_ean": f"{round(with_ean/total*100, 1)}%" if total > 0 else "0%",
        "esempi_titoli": samples
    }

results = [
    audit_clean_db("fluidra_clean.db", "products", "Fluidra"),
    audit_clean_db("intex_clean.db", "products", "Intex"),
    audit_clean_db("bestway_clean.db", "bestway_products", "Bestway")
]

print(json.dumps([r for r in results if r], indent=2))
