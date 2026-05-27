import sqlite3
import json
import os

def update_fluidra_prices():
    db_path = "fluidra_clean.db"
    audit_path = "audit_results_v2.json"
    
    if not os.path.exists(db_path) or not os.path.exists(audit_path):
        print("File per i prezzi non trovati.")
        return

    with open(audit_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updates = 0
    for item in audit_data:
        title = item.get('title')
        price_str = item.get('new_price')
        
        if title and price_str:
            # Pulizia prezzo (es: "1.962" -> 1962.0)
            try:
                price = float(price_str.replace('.', '').replace(',', '.'))
                # Cerchiamo per titolo esatto o parziale nel DB Fluidra
                cursor.execute("UPDATE products SET price_list = ? WHERE title = ? OR title LIKE ?", (price, title, f"%{title}%"))
                updates += cursor.rowcount
            except:
                continue

    conn.commit()
    conn.close()
    print(f"Aggiornamento prezzi Fluidra completato. {updates} record aggiornati.")

if __name__ == "__main__":
    update_fluidra_prices()
