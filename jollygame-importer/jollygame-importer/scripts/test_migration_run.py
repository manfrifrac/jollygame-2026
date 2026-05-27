import sqlite3, json, csv, requests

# 1. Carica il mapping file
mappings = []
with open('mapping_prodotti_jolly_gre_FINALE.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        mappings.append(row)

# 2. Carica i prodotti Shopify live
with open('jollygame-importer/jollygame-importer/shopify_products.json', 'r') as f:
    shop_products = json.load(f)
    sku_to_id = {p['sku']: p['id'] for p in shop_products if p.get('sku')}

# 3. Connetti DB Fluidra
conn = sqlite3.connect('fluidra_catalog.db')
cursor = conn.cursor()

# 4. Processa un campione
test_mappings = [m for m in mappings if m['SKU'] in sku_to_id][:3]

for m in test_mappings:
    parent_sku = m['SKU']
    product_id = sku_to_id[parent_sku]
    
    print(f"Test Mappatura per: {parent_sku} (ID: {product_id})")
    
    # Trova ricambi nel DB usando join corretti
    cursor.execute('''
        SELECT p.sku, p.title 
        FROM products p
        JOIN product_relations r ON p.sku = r.child_sku 
        WHERE r.parent_sku = ?
    ''', (parent_sku,))
    parts = cursor.fetchall()
    
    for c_sku, c_title in parts[:2]: # Max 2 ricambi per test
        print(f"  -> Ricambio trovato: {c_title} ({c_sku})")
        # Qui in futuro chiameremo la mutation per creare il Metaobject

conn.close()
