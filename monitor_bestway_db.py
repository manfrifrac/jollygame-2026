import sqlite3
import json
import os

def monitor():
    db_path = 'bestway_catalog.db'
    if not os.path.exists(db_path):
        print("Il database non esiste ancora. Lo scraper potrebbe essere all'inizio...")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Conteggio totale
    cursor.execute("SELECT COUNT(*) FROM bestway_products")
    total = cursor.fetchone()[0]
    
    # Statistiche qualità
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE ean IS NOT NULL")
    with_ean = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE price > 0")
    with_price = cursor.fetchone()[0]
    
    print("\n--- MONITORAGGIO BESTWAY DB ---")
    print(f"Prodotti totali: {total}")
    print(f"Prodotti con EAN: {with_ean}")
    print(f"Prodotti con Prezzo: {with_price}")
    
    # Ultimi 5 inseriti
    print("\nUltimi 5 prodotti inseriti:")
    cursor.execute("SELECT sku, title, category FROM bestway_products ORDER BY last_updated DESC LIMIT 5")
    for row in cursor.fetchall():
        print(f" - [{row[0]}] {row[1]} ({row[2]})")
    
    conn.close()

if __name__ == "__main__":
    monitor()
