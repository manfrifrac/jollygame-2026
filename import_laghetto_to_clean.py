import sqlite3
import csv
import os
import json

def import_laghetto():
    db_path = "fluidra_clean.db"
    csv_path = "laghetto_full_export_enriched.csv"
    
    if not os.path.exists(csv_path):
        print("CSV Laghetto non trovato.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        added = 0
        for row in reader:
            title = row['Titolo']
            # SKU per Laghetto: usiamo lo slug dell'URL se non c'è altro
            sku = row['URL'].rstrip('/').split('/')[-1].upper()
            
            # Uniamo le varie descrizioni
            full_desc = f"{row['Caratteristiche_Tecniche']}<br>{row['Scheda_Tecnica_Dati']}"

            # Trasformiamo immagini e docs in JSON
            images = json.dumps(row['Immagini'].split(','))
            docs = json.dumps([{"title": "Documentazione", "url": url} for url in row['PDF_Documenti'].split(',') if url])

            # Inseriamo nel DB
            cursor.execute('''
                INSERT INTO products (sku, title, price_list, description, images_json, docs_json, url, is_spare_part, taxonomy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    description = excluded.description,
                    images_json = excluded.images_json,
                    taxonomy = 'Piscine di Design > Laghetto'
            ''', (sku, title, 0.0, full_desc, images, docs, row['URL'], 0, 'Piscine di Design > Laghetto'))
            added += 1

    conn.commit()
    conn.close()
    print(f"Importazione Laghetto completata. {added} prodotti aggiunti/aggiornati.")

if __name__ == "__main__":
    import_laghetto()
