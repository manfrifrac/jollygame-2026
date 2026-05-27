import sqlite3
import os
import json

def get_best_column(available, suspects):
    for s in suspects:
        if s in available:
            return s
    for a in available:
        for s in suspects:
            if s in a.lower():
                return a
    return None

def analyze_db(db_path):
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']
    if not tables:
        return None
    
    # Prendo la tabella con più righe (probabilmente quella dei prodotti)
    best_table = None
    max_rows = -1
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        if count > max_rows:
            max_rows = count
            best_table = t

    table_name = best_table
    
    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    available_cols = [c[1] for c in cursor.fetchall()]
    
    mapping = {
        "sku": get_best_column(available_cols, ["sku", "code", "part_number", "id"]),
        "title": get_best_column(available_cols, ["title", "name", "descrizione", "label"]),
        "ean": get_best_column(available_cols, ["ean", "barcode", "gtin"]),
        "image": get_best_column(available_cols, ["image", "img", "image_url", "main_image", "thumbnail"])
    }
    
    mapping = {k: v for k, v in mapping.items() if v}
    cols_to_select = ", ".join(mapping.values())
    
    cursor.execute(f"SELECT {cols_to_select} FROM {table_name}")
    rows = cursor.fetchall()
    
    data = []
    ean_count = 0
    img_count = 0
    
    for row in rows:
        item = dict(zip(mapping.keys(), row))
        if item.get('ean') and str(item['ean']).strip() not in ['', 'None']:
            ean_count += 1
        if item.get('image') and str(item['image']).strip() not in ['', 'None']:
            img_count += 1
        data.append(item)
        
    conn.close()
    return {
        "db": db_path,
        "table": table_name,
        "total": max_rows,
        "with_ean": ean_count,
        "with_image": img_count,
        "mapping_used": mapping,
        "sample": data[:10] # Solo 10 per non intasare l'output
    }

results = {}
results["fluidra"] = analyze_db("fluidra_catalog.db")
results["intex"] = analyze_db("intex_catalog.db")
results["bestway"] = analyze_db("bestway_catalog.db")

print(json.dumps({k: v for k, v in results.items() if v}, indent=2))
