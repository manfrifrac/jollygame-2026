import sqlite3
import json
import os

def update_fluidra_prices_v2():
    db_path = "fluidra_clean.db"
    audit_path = "audit_results_v2.json"
    
    with open(audit_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updates = 0
    # Carichiamo tutti i prodotti Fluidra per fare il match in memoria (più veloce e flessibile)
    cursor.execute("SELECT sku, title FROM products")
    db_products = cursor.fetchall()
    
    for item in audit_data:
        audit_title = item.get('title', '').lower().strip()
        price_str = item.get('new_price')
        
        if not audit_title or not price_str: continue
        
        try:
            price = float(price_str.replace('.', '').replace(',', '.'))
            
            for sku, db_title in db_products:
                clean_db_title = str(db_title).lower().strip()
                
                # Match se il titolo dell'audit è contenuto nel titolo del DB o viceversa
                if audit_title in clean_db_title or clean_db_title in audit_title:
                    cursor.execute("UPDATE products SET price_list = ? WHERE sku = ?", (price, sku))
                    updates += cursor.rowcount
        except:
            continue

    conn.commit()
    conn.close()
    print(f"Aggiornamento prezzi Fluidra (v2) completato. {updates} record aggiornati.")

if __name__ == "__main__":
    update_fluidra_prices_v2()
