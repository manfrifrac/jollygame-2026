import sqlite3, json

# 1. Load Live Shopify Products (ID + SKU)
with open('jollygame-importer/jollygame-importer/shopify_products.json', 'r') as f:
    shop_products = json.load(f)
    # Creiamo una mappa: SKU -> Product ID
    sku_to_id = {p['sku']: p['id'] for p in shop_products if p.get('sku')}

# 2. Connetti DB Fluidra
conn = sqlite3.connect('fluidra_catalog.db')
cursor = conn.cursor()

# 3. Mappa relazioni e dettagli
# relations: parent_sku, child_sku
# products: sku, title, taxonomy (per categoria)
cursor.execute('SELECT r.parent_sku, r.child_sku, p.title, p.taxonomy FROM product_relations r JOIN products p ON r.child_sku = p.sku')
rows = cursor.fetchall()

dry_run_report = []

for p_sku, c_sku, c_title, c_taxonomy in rows:
    # Cerchiamo se il parent_sku (la piscina) è tra i prodotti live
    # Usiamo la logica di inclusione (partial match) dedotta prima
    parent_id = None
    for shop_sku, shop_id in sku_to_id.items():
        if p_sku in shop_sku or shop_sku in p_sku:
            parent_id = shop_id
            break
    
    if parent_id:
        dry_run_report.append({
            'Ricambio_Nome': c_title,
            'SKU_Ricambio': c_sku,
            'Categoria': c_taxonomy,
            'Piscina_ID_Collegata': parent_id
        })

# Stampa report
print(json.dumps(dry_run_report[:20], indent=2))
print(f"\n--- TOTALI: {len(dry_run_report)} ricambi pronti per la migrazione ---")
conn.close()
