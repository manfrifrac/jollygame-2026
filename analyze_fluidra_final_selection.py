import sqlite3
import json
import os

def analyze_fluidra_quality():
    if not os.path.exists("fluidra_catalog.db"):
        return "DB non trovato"

    conn = sqlite3.connect("fluidra_catalog.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Prendiamo solo i prodotti segnati come NON ricambi (is_spare_part = 0)
    cursor.execute("SELECT sku, title, ean, taxonomy, price_list FROM products WHERE is_spare_part = 0")
    rows = cursor.fetchall()

    spare_keywords = [
        "vite", "dado", "rondella", "guarnizione", "o-ring", "cavo", "tappo", "raccordo", 
        "valvola", "manopola", "molla", "cuscinetto", "spazzola", "tubo", "staffa", "piastra",
        "adattatore", "connettore", "ghiera", "perno", "bullone", "innesto"
    ]

    real_products = []
    technical_spares_disguised = []
    trash_or_unknown = []

    for r in rows:
        title = str(r['title']).lower()
        sku = str(r['sku']).upper()
        
        # Check if title contains spare keywords
        is_technical = any(kw in title for kw in spare_keywords)
        
        # Check SKU prefix (Fluidra specific)
        starts_with_r = sku.startswith('R')
        
        if is_technical or starts_with_r:
            technical_spares_disguised.append(dict(r))
        elif len(title) < 5 or r['sku'] in ["Aggiungi al carrello", "null"]:
            trash_or_unknown.append(dict(r))
        else:
            real_products.append(dict(r))

    conn.close()

    return {
        "totale_analizzati": len(rows),
        "prodotti_reali_probabili": len(real_products),
        "ricambi_mimetizzati": len(technical_spares_disguised),
        "spazzatura_o_dubbi": len(trash_or_unknown),
        "esempi_reali": real_products[:10],
        "esempi_ricambi_mimetizzati": technical_spares_disguised[:10]
    }

analysis = analyze_fluidra_quality()
print(json.dumps(analysis, indent=2))
