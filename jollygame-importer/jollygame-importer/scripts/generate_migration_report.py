import sqlite3, json

# Load Live SKUs
with open('jollygame-importer/jollygame-importer/live_skus.json', 'r') as f:
    live_skus = set(json.load(f))

conn = sqlite3.connect('fluidra_catalog.db')
cursor = conn.cursor()

# Get all relations where parent is live
cursor.execute('SELECT parent_sku, child_sku FROM product_relations')
relations = cursor.fetchall()

valid_links = []
for p_sku, c_sku in relations:
    if p_sku in live_skus:
        # Get spare part details
        cursor.execute('SELECT title, sku FROM products WHERE sku = ?', (c_sku,))
        part_info = cursor.fetchone()
        if part_info:
            valid_links.append({
                'parent_sku': p_sku,
                'part_title': part_info[0],
                'part_sku': part_info[1]
            })

# Save report
with open('valid_spare_parts.json', 'w') as f:
    json.dump(valid_links[:50], f, indent=2)

print(f"Found {len(valid_links)} valid spare parts for live products.")
print("Report saved to valid_spare_parts.json (first 50)")
conn.close()
