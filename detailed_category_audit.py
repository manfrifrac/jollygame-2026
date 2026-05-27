import sqlite3
import os
import json

def audit_brand(db_path, table, cat_col):
    if not os.path.exists(db_path): return None
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total products
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    total = cursor.fetchone()[0]
    
    # Coverage (escludendo valori nulli o placeholder)
    cursor.execute(f"SELECT {cat_col} FROM {table}")
    rows = cursor.fetchall()
    
    cats_found = [r[0] for r in rows if r[0] and str(r[0]).strip() not in ["", "None", "Senza Categoria", "Bestway Generic", "Piscine Intex"]]
    covered = len(cats_found)
    
    unique_cats = list(set(cats_found))
    
    max_depth = 0
    if unique_cats:
        # Analisi profondità (separatori comuni: > , / , | )
        for c in unique_cats:
            depth = len(c.replace(" > ", ">").replace("/", ">").replace("|", ">").split(">"))
            if depth > max_depth: max_depth = depth
            
    conn.close()
    return {
        "total": total,
        "covered": covered,
        "coverage_perc": round((covered/total)*100, 1) if total > 0 else 0,
        "unique_categories": len(unique_cats),
        "max_depth": max_depth,
        "sample_cats": unique_cats[:5]
    }

results = {
    "Fluidra": audit_brand("fluidra_catalog.db", "products", "taxonomy"),
    "Intex": audit_brand("intex_deep_catalog.db", "products", "categories"),
    "Bestway": audit_brand("bestway_catalog.db", "bestway_products", "category")
}

print(json.dumps({k: v for k, v in results.items() if v}, indent=2))
