import sqlite3
import csv
import os
import json

def import_zodiac():
    db_path = "fluidra_clean.db"
    csv_path = "zodiac_enriched_data.csv"
    
    if not os.path.exists(csv_path):
        print("CSV Zodiac non trovato.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        added = 0
        for row in reader:
            # Estraiamo lo SKU dal titolo o URL (Zodiac solitamente ha SKU nel titolo)
            title = row['Titolo']
            sku = title.split(' ')[0] # Rozzo ma efficace per Zodiac se non c'è colonna SKU
            
            price_raw = row['Prezzo'].replace('€', '').replace('.', '').replace(',', '.').strip()
            try:
                price = float(price_raw) if price_raw else 0.0
            except:
                price = 0.0

            # Trasformiamo immagini e docs in JSON
            images = json.dumps(row['Immagini'].split(','))
            docs = json.dumps([{"title": "Manuale", "url": url} for url in row['PDF_Documents'].split(',') if url])

            # Inseriamo nel DB
            cursor.execute('''
                INSERT INTO products (sku, title, price_list, description, images_json, docs_json, url, is_spare_part, taxonomy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    price_list = excluded.price_list,
                    description = excluded.description,
                    images_json = excluded.images_json,
                    taxonomy = 'Robot Pulitori > Zodiac'
            ''', (sku, title, price, row['Descrizione_HTML'], images, docs, row['URL'], 0, 'Robot Pulitori > Zodiac'))
            added += 1

    conn.commit()
    conn.close()
    print(f"Importazione Zodiac completata. {added} prodotti aggiunti/aggiornati.")

if __name__ == "__main__":
    import_zodiac()
