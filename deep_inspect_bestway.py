import sqlite3
import json
import os
import re

def analyze_fluidra_segments():
    db_path = "fluidra_clean.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Carichiamo tutti i record non flaggati come ricambi (is_spare_part = 0)
    cursor.execute("SELECT sku, title, taxonomy, ean, images_json FROM products WHERE is_spare_part = 0")
    rows = cursor.fetchall()
    
    technical_keywords = [
        "vite", "dado", "rondella", "guarnizione", "o-ring", "bullone", "perno", 
        "tappo", "molla", "staffa", "piastra", "raccordo", "manopola", "manometro",
        "tubo", "cavo", "adattatore", "connettore", "ghiera", "innesto", "cuscinetto"
    ]
    
    commercial_products = []
    technical_spares = []
    garbage = []

    for r in rows:
        title = str(r['title']).lower()
        sku = str(r['sku']).upper()
        taxonomy = str(r['taxonomy']).lower()
        
        # Criterio A: Titolo puramente numerico o troppo corto
        if re.match(r'^\d+$', title.replace(" ", "")) or len(title) < 5:
            garbage.append(dict(r))
            continue
            
        # Criterio B: Parole chiave tecniche (ferramenta)
        is_tech = any(kw in title for kw in technical_keywords) or any(kw in taxonomy for kw in technical_keywords)
        
        # Criterio C: Prefisso SKU "R" (Spesso indica Replacement/Ricambio in Fluidra)
        is_r_sku = sku.startswith('R')
        
        if is_tech or is_r_sku:
            technical_spares.append(dict(r))
        else:
            commercial_products.append(dict(r))

    conn.close()
    
    return {
        "commercial_total": len(commercial_products),
        "technical_total": len(technical_spares),
        "garbage_total": len(garbage),
        "commercial_samples": [f"{p['sku']} | {p['title']} ({p['taxonomy']})" for p in commercial_products[:20]],
        "technical_samples": [f"{p['sku']} | {p['title']} ({p['taxonomy']})" for p in technical_spares[:20]]
    }

analysis = analyze_fluidra_segments()
print(json.dumps(analysis, indent=2))
