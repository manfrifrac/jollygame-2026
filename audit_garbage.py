import sqlite3
import os
import csv
import json

def analyze_garbage():
    garbage_list = []
    
    # Mapping corretti per ogni DB
    dbs = {
        "fluidra": ("fluidra_catalog.db", "products", {"sku": "sku", "title": "title", "ean": "ean", "img": "images_json"}),
        "intex": ("intex_deep_catalog.db", "products", {"sku": "sku", "title": "title", "ean": "ean", "img": "images"}),
        "bestway": ("bestway_catalog.db", "bestway_products", {"sku": "sku", "title": "title", "ean": "ean", "img": "images"})
    }

    for brand, (db_path, table, mapping) in dbs.items():
        if not os.path.exists(db_path): continue
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cols = ", ".join(mapping.values())
        cursor.execute(f"SELECT {cols} FROM {table}")
        rows = cursor.fetchall()
        
        for r in rows:
            data = dict(r)
            sku = str(data.get(mapping['sku'], '')).strip()
            title = str(data.get(mapping['title'], '')).strip()
            ean = str(data.get(mapping['ean'], '')).strip()
            img = str(data.get(mapping['img'], '')).strip()
            
            reasons = []
            
            # Criterio 1: SKU è un testo di interfaccia (Scraper Fail)
            bad_skus = ["aggiungi al carrello", "in stock", "disponibile", "vedi dettagli", "esaurito", "null", "none", "seleziona"]
            if sku.lower() in bad_skus or len(sku) < 2:
                reasons.append("SKU_ERRATO")
            
            # Criterio 2: Titolo vuoto o insignificante
            if not title or title.lower() in ["none", "null", ".", "---", "test", "label", "titolo"] or len(title) < 3:
                reasons.append("TITOLO_INVALIDO")
            
            # Criterio 3: Incompleto (No EAN e No Foto)
            has_no_ean = not ean or ean.lower() in ["none", "null", ""]
            has_no_img = not img or img.lower() in ["none", "null", "", "[]"]
            if has_no_ean and has_no_img:
                reasons.append("MINIMO_DATI_NON_RAGGIUNTO")

            if reasons:
                garbage_list.append({
                    "Brand": brand,
                    "SKU": sku,
                    "Titolo": title,
                    "EAN": ean,
                    "Immagine": img[:50] + "..." if len(img) > 50 else img,
                    "Motivo": " | ".join(reasons)
                })
        conn.close()
    
    if garbage_list:
        with open('audit_prodotti_spazzatura.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=garbage_list[0].keys())
            writer.writeheader()
            writer.writerows(garbage_list)
    
    return len(garbage_list)

count = analyze_garbage()
print(f"Analisi completata: {count} prodotti sospetti salvati in audit_prodotti_spazzatura.csv")
