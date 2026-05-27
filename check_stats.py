import sqlite3
import os
import json

def refined_audit():
    results = []
    
    # 1. FLUIDRA: Solo quelli con prezzo > 0 (i 62 "Gold")
    conn_f = sqlite3.connect("fluidra_clean.db")
    cursor_f = conn_f.cursor()
    cursor_f.execute("SELECT COUNT(*) FROM products WHERE price_list > 0 AND is_spare_part = 0")
    fluidra_count = cursor_f.fetchone()[0]
    conn_f.close()
    
    # 2. INTEX & BESTWAY: Solo Piscine e Spa, escludendo gonfiabili e altro
    # Keywords per inclusione
    inc_piscine = ["piscina", "pool", "frame", "xtr", "prism", "graphite"]
    inc_spa = ["spa", "idromassaggio", "purespa", "lay-z-spa"]
    
    # Keywords per esclusione (non vogliamo materassini, giochi, kayak, airbeds)
    exc_gonfiabili = ["airbed", "materassino", "canotto", "kayak", "gioco", "toy", "jumping", "castello", "amaca", "poltrona", "zattera", "beach", "pallone"]

    def filter_brand(db_path, table, brand, price_col):
        if not os.path.exists(db_path): return 0, []
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table} WHERE {price_col} > 0 AND is_spare_part = 0")
        rows = cursor.fetchall()
        
        filtered = []
        for r in rows:
            title = str(r['title']).lower()
            
            # Check inclusion
            is_pool_or_spa = any(k in title for k in inc_piscine) or any(k in title for k in inc_spa)
            # Check exclusion
            is_garbage = any(k in title for k in exc_gonfiabili)
            
            if is_pool_or_spa and not is_garbage:
                filtered.append(dict(r))
        
        conn.close()
        return len(filtered), filtered[:5]

    intex_count, intex_samples = filter_brand("intex_clean.db", "products", "Intex", "price")
    bestway_count, bestway_samples = filter_brand("bestway_clean.db", "bestway_products", "Bestway", "price")

    return {
        "Fluidra_Gold": fluidra_count,
        "Intex_Piscine_Spa": intex_count,
        "Bestway_Piscine_Spa": bestway_count,
        "Total_Active_Catalog": fluidra_count + intex_count + bestway_count,
        "Samples_Intex": [s['title'] for s in intex_samples],
        "Samples_Bestway": [s['title'] for s in bestway_samples]
    }

print(json.dumps(refined_audit(), indent=2))
