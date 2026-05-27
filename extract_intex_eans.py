import sqlite3
import urllib.request
import re
import time

def extract_and_save_eans():
    conn = sqlite3.connect("intex_catalog.db")
    cursor = conn.cursor()

    # 1. Add EAN column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN ean TEXT")
        print("Aggiunta colonna 'ean' al database.")
    except sqlite3.OperationalError:
        print("La colonna 'ean' esiste già.")

    # 2. Get all products from Intex Italia
    cursor.execute("SELECT id, url, title FROM products WHERE source = 'intex_italia' AND (ean IS NULL OR ean = '')")
    products = cursor.fetchall()

    print(f"\nInizio estrazione EAN per {len(products)} prodotti di Intex Italia...")
    
    success_count = 0
    
    for p_id, url, title in products:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
                
            # Cerca EAN a 13 cifre (filtra timestamp falsi positivi)
            potential_eans = re.findall(r'(?<!\d)(\d{13})(?!\d)', html)
            filtered_eans = [e for e in potential_eans if not e.startswith('16') and not e.startswith('17')]
            
            if filtered_eans:
                # Prendi il primo EAN trovato
                ean = filtered_eans[0]
                cursor.execute("UPDATE products SET ean = ? WHERE id = ?", (ean, p_id))
                print(f"[OK] Trovato EAN {ean} per: {title[:40]}...")
                success_count += 1
            else:
                print(f"[MISS] Nessun EAN trovato per: {title[:40]}...")
                
            # Pausa per non sovraccaricare il server
            time.sleep(1)
            
        except Exception as e:
            print(f"[ERRORE] su {url}: {e}")

    conn.commit()
    conn.close()
    
    print(f"\nEstrazione completata. Aggiornati {success_count} prodotti con EAN.")

if __name__ == "__main__":
    extract_and_save_eans()
