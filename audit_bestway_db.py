import sqlite3
import json

def run_audit():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    
    print("=== AUDIT CATALOGO BESTWAY 2026 ===")
    
    # 1. Totali
    cursor.execute("SELECT COUNT(DISTINCT sku) FROM bestway_products")
    total_unique = cursor.fetchone()[0]
    print(f"\nProdotti Singoli (SKU unici): {total_unique}")
    
    # 2. Qualità Dati
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE ean IS NOT NULL AND ean != ''")
    with_ean = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE price > 0")
    with_price = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE images IS NOT NULL AND images != ''")
    with_images = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE description_html IS NOT NULL AND description_html != ''")
    with_desc = cursor.fetchone()[0]

    print(f"\n--- Integrità Dati ---")
    print(f"EAN presenti: {with_ean} ({round(with_ean/total_unique*100, 1)}%)")
    print(f"Prezzi validi (>0): {with_price} ({round(with_price/total_unique*100, 1)}%)")
    print(f"Immagini presenti: {with_images} ({round(with_images/total_unique*100, 1)}%)")
    print(f"Descrizioni presenti: {with_desc} ({round(with_desc/total_unique*100, 1)}%)")
    
    # 3. Audit Categorie
    print(f"\n--- Distribuzione per Categoria ---")
    cursor.execute("SELECT category, COUNT(*) as count FROM bestway_products GROUP BY category ORDER BY count DESC")
    categories = cursor.fetchall()
    for cat, count in categories[:15]: # Prime 15
        print(f" - {cat}: {count} prodotti")
    
    # 4. Controllo Dati Tecnici (Specs)
    cursor.execute("SELECT specs_json FROM bestway_products LIMIT 100")
    specs_samples = cursor.fetchall()
    avg_specs = sum(len(json.loads(s[0])) for s in specs_samples) / len(specs_samples)
    print(f"\nMedia campi tecnici per prodotto: {round(avg_specs, 1)}")

    # 5. Esempi di prodotti senza EAN (per controllo manuale)
    if with_ean < total_unique:
        print(f"\n--- Alert: Prodotti senza EAN (Top 5) ---")
        cursor.execute("SELECT sku, title FROM bestway_products WHERE ean IS NULL OR ean = '' LIMIT 5")
        for sku, title in cursor.fetchall():
            print(f" [!] {sku} - {title}")

    conn.close()

if __name__ == "__main__":
    run_audit()
