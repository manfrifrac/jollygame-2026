import sqlite3
import sys

# Forza l'encoding UTF-8 per evitare errori su Windows
sys.stdout.reconfigure(encoding='utf-8')

def check_progress():
    try:
        conn = sqlite3.connect('fluidra_catalog.db')
        cursor = conn.cursor()
        
        # Conteggio totale
        cursor.execute("SELECT count(*) FROM products")
        total = cursor.fetchone()[0]
        
        # Conteggio EAN validi
        cursor.execute("SELECT count(*) FROM products WHERE ean IS NOT NULL AND ean != 'N/A'")
        ean_count = cursor.fetchone()[0]
        
        # Conteggio prodotti con titolo pulito (non solo codice numerico)
        cursor.execute("SELECT count(*) FROM products WHERE title IS NOT NULL AND title NOT GLOB '[0-9]*'")
        title_count = cursor.fetchone()[0]
        
        # Ultime 5 righe aggiornate
        cursor.execute("SELECT url, ean, title FROM products WHERE ean IS NOT NULL AND ean != 'N/A' ORDER BY rowid DESC LIMIT 5")
        last_updates = cursor.fetchall()
        
        print(f"📊 REPORT PROGRESSO FLUIDRA")
        print(f"---------------------------")
        print(f"✅ EAN RECUPERATI: {ean_count} su {total} ({(ean_count/total*100):.2f}%)")
        print(f"✅ TITOLI PULITI : {title_count}")
        print(f"\n🕒 ULTIMI AGGIORNAMENTI:")
        for url, ean, title in last_updates:
            # Sostituisce caratteri non stampabili per sicurezza
            safe_title = title.encode('ascii', 'replace').decode('ascii')
            print(f"   - {ean} | {safe_title}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == '__main__':
    check_progress()