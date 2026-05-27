import json
import sqlite3
import os

def run_analysis():
    variants_path = "jollygame-importer/jollygame-importer/all_shopify_variants.json"
    if not os.path.exists(variants_path):
        print("File all_shopify_variants.json non trovato.")
        return

    with open(variants_path, 'r', encoding='utf-8') as f:
        variants = json.load(f)

    # Connessione DB
    fluidra_conn = sqlite3.connect('fluidra_catalog.db')
    fluidra_cursor = fluidra_conn.cursor()

    bestway_conn = sqlite3.connect('bestway_catalog.db')
    bestway_cursor = bestway_conn.cursor()

    updates = []
    fixed_count = 0

    for v in variants:
        sku = v.get('sku')
        if not sku:
            continue
            
        found_price = None
        
        # 1. Ricerca in Fluidra (Exact then Partial)
        fluidra_cursor.execute("SELECT price_list FROM products WHERE sku = ?", (sku,))
        row = fluidra_cursor.fetchone()
        if not row:
            # Prova partial se numerico corto
            if len(sku) >= 5 and sku.isdigit():
                fluidra_cursor.execute("SELECT price_list FROM products WHERE sku LIKE ?", (f"%{sku}%",))
                row = fluidra_cursor.fetchone()
        
        if row and row[0]:
            found_price = row[0]

        # 2. Ricerca in Bestway
        if not found_price:
            bestway_cursor.execute("SELECT price FROM bestway_products WHERE sku = ?", (sku,))
            row = bestway_cursor.fetchone()
            if row and row[0]:
                found_price = row[0]

        # Se abbiamo trovato un prezzo e quello attuale è 0 o diverso
        current_p = float(v['current_price'])
        if found_price and (current_p <= 0 or abs(current_p - found_price) > 0.01):
            updates.append({
                "product_id": v['product_id'],
                "variant_id": v['variant_id'],
                "sku": sku,
                "old_price": current_p,
                "new_price": found_price,
                "inventoryPolicy": "CONTINUE"
            })
            if current_p <= 0:
                fixed_count += 1
        else:
            # Anche se non abbiamo il prezzo, attiviamo il "Continue selling" per sbloccare il magazzino
            updates.append({
                "product_id": v['product_id'],
                "variant_id": v['variant_id'],
                "sku": sku,
                "old_price": current_p,
                "new_price": current_p,
                "inventoryPolicy": "CONTINUE"
            })

    fluidra_conn.close()
    bestway_conn.close()

    with open("jollygame-importer/jollygame-importer/variants_update_plan.json", "w", encoding="utf-8") as f:
        json.dump(updates, f, indent=2)

    print(f"📊 ANALISI COMPLETATA:")
    print(f"✅ Varianti da aggiornare (Prezzo o Policy): {len(updates)}")
    print(f"💰 Prezzi 0.00 corretti con dati DB: {fixed_count}")

if __name__ == "__main__":
    run_analysis()
