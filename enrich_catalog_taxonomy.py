import sqlite3
import json
import os
import sys

def update_taxonomy():
    db_path = "fluidra_catalog.db"
    map_path = "fluidra_product_links_map.json"
    
    if not os.path.exists(db_path) or not os.path.exists(map_path):
        print("File mancanti.")
        return

    print("Caricamento mappa categorie...")
    with open(map_path, "r", encoding="utf-8") as f:
        cat_map = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Prepariamo i dati
    data_to_update = []
    for cat_name, urls in cat_map.items():
        for url in urls:
            clean_url = url.split('?')[0]
            data_to_update.append((cat_name, clean_url))

    total = len(data_to_update)
    print(f"Inizio aggiornamento di {total} link...")
    
    updates = 0
    # Usiamo executemany per la massima velocità
    cursor.execute("BEGIN TRANSACTION")
    try:
        # Aggiornamento massivo
        cursor.executemany("UPDATE products SET taxonomy = ? WHERE url = ?", data_to_update)
        updates = cursor.rowcount
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Errore: {e}")

    conn.close()
    print(f"\n✅ Completato! {total} record processati.")

if __name__ == "__main__":
    update_taxonomy()
