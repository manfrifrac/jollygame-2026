import sqlite3
import re
import json

def clean_and_verify():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    
    # 1. Recupero dati per analisi
    cursor.execute("SELECT sku, ean, title, images, specs_json FROM bestway_products")
    rows = cursor.fetchall()
    
    cleaned_count = 0
    issues_found = {
        "junk_in_sku": 0,
        "invalid_ean": 0,
        "broken_images": 0,
        "missing_specs": 0
    }

    print("--- Inizio Pulizia e Validazione ---")

    for row in rows:
        sku, ean, title, images, specs_json = row
        new_sku = sku
        new_ean = ean
        
        # A. Pulizia SKU (Rimuove CSS/JS se presenti)
        if "{" in sku or "." in sku and "_" in sku:
            # Se lo SKU sembra CSS, proviamo a recuperarlo dal JSON delle specifiche
            specs = json.loads(specs_json)
            new_sku = specs.get("sku", sku)
            if "{" in new_sku: # Se è ancora sporco, lo puliamo con regex
                match = re.search(r'([A-Z0-9\-]{4,})', new_sku)
                new_sku = match.group(1) if match else new_sku
            issues_found["junk_in_sku"] += 1

        # B. Pulizia EAN (Deve essere solo numerico)
        if ean:
            clean_ean = re.sub(r'[^0-9]', '', str(ean))
            if clean_ean != str(ean):
                new_ean = clean_ean
                issues_found["invalid_ean"] += 1
        
        # C. Verifica Immagini
        if not images or "placeholder" in images.lower():
            issues_found["broken_images"] += 1
            
        # D. Verifica Specifiche
        if not specs_json or specs_json == "{}":
            issues_found["missing_specs"] += 1

        # Aggiornamento se necessario
        if new_sku != sku or new_ean != ean:
            cursor.execute("UPDATE bestway_products SET sku = ?, ean = ? WHERE sku = ?", (new_sku, new_ean, sku))
            cleaned_count += 1

    conn.commit()
    
    print(f"\nRisultati della pulizia:")
    print(f"- Record aggiornati/puliti: {cleaned_count}")
    print(f"- Junk rimosso dagli SKU: {issues_found['junk_in_sku']}")
    print(f"- EAN corretti: {issues_found['invalid_ean']}")
    print(f"- Prodotti con immagini sospette: {issues_found['broken_images']}")
    print(f"- Prodotti senza specifiche tecniche: {issues_found['missing_specs']}")

    # Check finale EAN (quanti ne mancano davvero ora?)
    cursor.execute("SELECT COUNT(*) FROM bestway_products WHERE ean IS NULL OR ean = ''")
    missing_ean = cursor.fetchone()[0]
    print(f"- EAN ancora mancanti: {missing_ean}")

    conn.close()

if __name__ == "__main__":
    clean_and_verify()
