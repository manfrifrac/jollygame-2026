import sqlite3
import os
import json

def audit_final_gold_selection():
    dbs = [
        ("fluidra_clean.db", "products", "Fluidra", "price_list", "taxonomy", "images_json"),
        ("intex_clean.db", "products", "Intex", "price", "categories", "images"),
        ("bestway_clean.db", "bestway_products", "Bestway", "price", "category", "images")
    ]
    
    overall_report = []

    for db_path, table, brand, p_col, c_col, i_col in dbs:
        if not os.path.exists(db_path): continue
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table}")
        rows = [dict(r) for r in cursor.fetchall()]
        total = len(rows)
        
        if total == 0:
            overall_report.append({"Brand": brand, "Status": "Vuoto dopo filtro"})
            conn.close()
            continue

        prices = [float(r[p_col]) for r in rows if r[p_col]]
        with_ean = len([r for r in rows if r.get('ean') and len(str(r['ean'])) > 5])
        
        # Check descriptions
        desc_col = 'description' if brand != 'Bestway' else 'description_html'
        with_desc = len([r for r in rows if r.get(desc_col) and len(str(r[desc_col])) > 50])
        
        # Check images (already filtered, but let's count)
        with_img = len([r for r in rows if r.get(i_col) and r[i_col] != '[]' and r[i_col] != ''])

        overall_report.append({
            "Brand": brand,
            "Prodotti": total,
            "Prezzo Medio": f"{round(sum(prices)/len(prices), 2)} €" if prices else "0",
            "Prezzo Min": f"{min(prices)} €" if prices else "0",
            "Prezzo Max": f"{max(prices)} €" if prices else "0",
            "Copertura EAN": f"{round(with_ean/total*100, 1)}%",
            "Schede Rich (>50 char)": f"{round(with_desc/total*100, 1)}%",
            "Immagini OK": f"{round(with_img/total*100, 1)}%"
        })
        conn.close()

    return overall_report

report = audit_final_gold_selection()
print(json.dumps(report, indent=2))
