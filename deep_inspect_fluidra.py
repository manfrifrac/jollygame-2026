import sqlite3
import json
import os
import re

def deep_fluidra_analysis():
    db_path = "fluidra_clean.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Quanti sono segnati come 'is_spare_part = 0'?
    cursor.execute("SELECT COUNT(*) FROM products WHERE is_spare_part = 0")
    total_not_spare = cursor.fetchone()[0]
    
    # 2. Quanti di questi hanno un 'esploso' collegato (sono i "Padri" tecnici)?
    cursor.execute("SELECT COUNT(DISTINCT parent_sku) FROM product_relations")
    fathers_count = cursor.fetchone()[0]
    
    # 3. Analizziamo le categorie per capire cosa sono i 9.000 record
    cursor.execute("""
        SELECT taxonomy, COUNT(*) as c 
        FROM products 
        WHERE is_spare_part = 0 
        GROUP BY taxonomy 
        ORDER BY c DESC 
        LIMIT 15
    """)
    top_cats = [dict(r) for r in cursor.fetchall()]
    
    # 4. Vediamo quanti prodotti "commerciali" (non ferramenta) abbiamo con foto
    # Escludiamo parole chiave da ferramenta
    technical_keywords = ["vite", "dado", "rondella", "guarnizione", "o-ring", "bullone", "perno", "tappo", "cavo", "tubo"]
    
    cursor.execute("SELECT sku, title, taxonomy, price_list, ean, images_json FROM products WHERE is_spare_part = 0")
    rows = cursor.fetchall()
    
    finished_goods = []
    hidden_spares = []
    
    for r in rows:
        title = str(r['title']).lower()
        if any(kw in title for kw in technical_keywords):
            hidden_spares.append(dict(r))
        else:
            # Se ha un'immagine e un titolo sensato, lo consideriamo un Prodotto Finito
            if r['images_json'] and r['images_json'] != '[]' and len(title) > 8:
                finished_goods.append(dict(r))

    conn.close()
    
    return {
        "totale_nel_db": 11550,
        "identificati_come_non_ricambi": total_not_spare,
        "prodotti_padri_di_esplosi": fathers_count,
        "prodotti_finiti_con_foto_e_titolo_valido": len(finished_goods),
        "ricambi_mimetizzati_trovati_nei_prodotti": len(hidden_spares),
        "top_categorie_fluidra": top_cats,
        "esempi_prodotti_finiti": [f"{p['sku']} | {p['title']}" for p in finished_goods[:15]]
    }

print(json.dumps(deep_fluidra_analysis(), indent=2))
