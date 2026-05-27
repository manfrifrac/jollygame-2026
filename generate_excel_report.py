import sqlite3
import csv
import os
import json

def generate_full_report():
    output_file = "REPORT_REVISIONE_JOLLYGAME_2026.csv"
    
    # 1. Definiamo i database e le logiche di estrazione
    dbs = [
        ("fluidra_clean.db", "products", "Fluidra"),
        ("intex_clean.db", "products", "Intex"),
        ("bestway_clean.db", "bestway_products", "Bestway")
    ]
    
    # Keywords per categorizzazione rapida nel report
    inc_piscine = ["piscina", "pool", "frame", "xtr", "prism", "graphite", "acciaio", "legno"]
    inc_spa = ["spa", "idromassaggio", "purespa", "lay-z-spa"]
    inc_macchine = ["robot", "pulitore", "pompa", "filtro", "cloratore", "elettrolisi", "vortex", "cnx"]

    all_data = []

    for db_path, table, brand in dbs:
        if not os.path.exists(db_path): continue
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Estraiamo tutti i non-ricambi (o quelli che abbiamo identificato come potenziali prodotti)
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        for r in rows:
            data = dict(r)
            title = str(data.get('title', '')).strip()
            sku = str(data.get('sku', '')).strip()
            
            # Normalizzazione Prezzo
            p_val = data.get('price_list') if brand == 'Fluidra' else data.get('price')
            try: price = float(p_val) if p_val else 0.0
            except: price = 0.0
            
            # Normalizzazione Immagine
            img = ""
            if brand == 'Fluidra':
                try: 
                    imgs = json.loads(data.get('images_json', '[]'))
                    img = imgs[0] if imgs else ""
                except: img = ""
            elif brand == 'Intex':
                img = data.get('image_url', data.get('images', ''))
            else:
                img = data.get('images', '').split(',')[0]

            # Categorizzazione suggerita per aiutare il cliente
            category_sugg = "Accessori/Ricambi"
            title_l = title.lower()
            if any(k in title_l for k in inc_piscine): category_sugg = "PISCINE"
            elif any(k in title_l for k in inc_spa): category_sugg = "SPA"
            elif any(k in title_l for k in inc_macchine): category_sugg = "MACCHINE"

            # Identificazione "Qualità"
            quality_score = "BASSA"
            if price > 0 and img and len(str(data.get('ean', ''))) > 5:
                quality_score = "ALTA (Pronto)"
            elif img and (price > 0 or len(title) > 20):
                quality_score = "MEDIA (Manca EAN o Prezzo)"

            all_data.append({
                "BRAND": brand,
                "SKU": sku,
                "EAN": data.get('ean', 'N/A'),
                "TITOLO": title,
                "PREZZO_PUBBLICO": f"{price} €" if price > 0 else "0.00 € (Mancante)",
                "CATEGORIA_ORIGINALE": data.get('taxonomy') or data.get('categories') or data.get('category', ''),
                "TIPO_SUGGERITO": category_sugg,
                "SCORE_QUALITA": quality_score,
                "URL_IMMAGINE": img,
                "DESCRIZIONE_BREVE": str(data.get('description', data.get('description_html', '')))[:150].replace('\n', ' '),
                "URL_ORIGINALE": data.get('url', '')
            })
        conn.close()

    # Scrittura CSV
    if all_data:
        keys = all_data[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f: # utf-8-sig per compatibilità Excel
            writer = csv.DictWriter(f, fieldnames=keys, delimiter=';') # Punto e virgola per Excel Italiano
            writer.writeheader()
            writer.writerows(all_data)
        return output_file, len(all_data)
    return None, 0

file_path, total = generate_full_report()
if file_path:
    print(f"✅ Report generato con successo: {file_path}")
    print(f"📊 Totale prodotti inclusi per la revisione: {total}")
else:
    print("❌ Errore nella generazione del report.")
