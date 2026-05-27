import sqlite3
import json

def run_audit():
    conn = sqlite3.connect('fluidra_catalog.db')
    c = conn.cursor()

    # Conteggio Totale
    c.execute("SELECT COUNT(*) FROM products")
    total = c.fetchone()[0]
    
    # Conteggio per Tipo
    c.execute("SELECT COUNT(*) FROM products WHERE is_spare_part=1")
    spares = c.fetchone()[0]
    main_products = total - spares

    # Analisi Campi (Quanti sono NON nulli o NON default)
    fields = {
        "SKU (Identificativo)": "COUNT(*)",
        "EAN (Codice a barre)": "SUM(CASE WHEN ean IS NOT NULL AND ean != 'N/A' THEN 1 ELSE 0 END)",
        "Titolo Esteso": "SUM(CASE WHEN title IS NOT NULL AND title != 'N/A' AND title != '' THEN 1 ELSE 0 END)",
        "Prezzo Netto": "SUM(CASE WHEN price_net > 0 THEN 1 ELSE 0 END)",
        "Stock Italia": "SUM(CASE WHEN stock_italy > 0 THEN 1 ELSE 0 END)",
        "Immagini Gallery": "SUM(CASE WHEN images_json != '[]' THEN 1 ELSE 0 END)",
        "Documenti PDF": "SUM(CASE WHEN docs_json != '[]' THEN 1 ELSE 0 END)",
        "Schemi Esplosi (Mappe)": "SUM(CASE WHEN diagram_url IS NOT NULL THEN 1 ELSE 0 END)",
        "Specifiche Tecniche": "SUM(CASE WHEN specs_json != '{}' AND specs_json != '[]' THEN 1 ELSE 0 END)"
    }

    results = {}
    for label, query in fields.items():
        c.execute(f"SELECT {query} FROM products")
        val = c.fetchone()[0]
        results[label] = val

    print("==================================================")
    print("📊 AUDIT COMPLETO CATALOGO FLUIDRA PRO")
    print("==================================================")
    print(f"Record totali nel database: {total}")
    print(f"  - Prodotti Principali: {main_products}")
    print(f"  - Ricambi (dall'esploso): {spares}")
    print("--------------------------------------------------")
    print("COMPILAZIONE CAMPI (Record con dati validi):")
    
    for label, count in results.items():
        percentage = (count / total) * 100
        print(f"✅ {label:25}: {count:5} ({percentage:5.1f}%)")

    # Prodotti "Perfetti" (con Titolo, Prezzo e almeno una Foto)
    c.execute("""
        SELECT COUNT(*) FROM products 
        WHERE title != 'N/A' AND price_net > 0 AND images_json != '[]'
    """)
    perfect = c.fetchone()[0]
    print("--------------------------------------------------")
    print(f"🏆 Prodotti con scheda completa (Titolo+Prezzo+Foto): {perfect}")
    print("==================================================")

    conn.close()

if __name__ == "__main__":
    run_audit()
