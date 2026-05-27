import sqlite3, json, csv

# 1. Carica il mapping SKU -> Shopify ID
sku_to_shopify_id = {}
with open('mapping_prodotti_jolly_gre_FINALE.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['SKU']:
            # Cerchiamo l'ID dai prodotti precedentemente esportati
            pass

# Ricarichiamo gli ID correttamente dal file JSON
with open('jollygame-importer/jollygame-importer/shopify_products.json', 'r') as f:
    shop_products = json.load(f)
    shopify_sku_map = {p['sku']: p['id'] for p in shop_products if p.get('sku')}

# 2. Connetti DB Fluidra
conn = sqlite3.connect('fluidra_catalog.db')
cursor = conn.cursor()

# 3. Creiamo un report di tutte le associazioni valide
# parent_sku (da fluidra) -> child_sku (ricambio)
cursor.execute('SELECT parent_sku, child_sku, title FROM products JOIN product_relations ON sku=child_sku')
rows = cursor.fetchall()

migration_plan = {}

for p_sku, c_sku, c_title in rows:
    # Cerchiamo se il parent_sku (Fluidra) è collegabile a un prodotto Shopify
    # Usiamo il match parziale validato
    for shop_sku, shop_id in shopify_sku_map.items():
        if p_sku in shop_sku or shop_sku in p_sku:
            migration_plan.setdefault(shop_id, []).append({
                'nome': c_title,
                'sku': c_sku
            })
            break

with open('migration_plan.json', 'w') as f:
    json.dump(migration_plan, f, indent=2)

print(f"Migrazione pianificata per {len(migration_plan)} prodotti.")
conn.close()
