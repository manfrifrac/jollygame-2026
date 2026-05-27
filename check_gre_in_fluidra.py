import sqlite3
import os

def check_gre():
    db_path = "fluidra_clean.db"
    if not os.path.exists(db_path):
        print("DB non trovato.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Gre pool SKUs often start with KIT or are 5-6 characters
    cursor.execute("SELECT COUNT(*) FROM products WHERE taxonomy LIKE '%Gre%' OR title LIKE '%Gre%'")
    count_text = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE sku LIKE 'KIT%'")
    count_kit = cursor.fetchone()[0]
    
    print(f"Prodotti con testo 'Gre': {count_text}")
    print(f"Prodotti con SKU 'KIT...': {count_kit}")
    
    if count_text > 0:
        cursor.execute("SELECT sku, title, taxonomy FROM products WHERE taxonomy LIKE '%Gre%' OR title LIKE '%Gre%' LIMIT 5")
        for r in cursor.fetchall():
            print(f"  {r}")
            
    conn.close()

if __name__ == "__main__":
    check_gre()
