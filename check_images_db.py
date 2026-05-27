import sqlite3

conn = sqlite3.connect('fluidra_clean.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM products WHERE images_json != '[]' AND images_json != '' AND images_json IS NOT NULL;")
print("Total products with images:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM product_relations;")
print("Total product relations:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM product_relations pr JOIN products p ON pr.child_sku = p.sku;")
print("Total child products found in products table:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM product_relations pr JOIN products p ON pr.child_sku = p.sku WHERE p.images_json != '[]';")
print("Total child products with images:", cursor.fetchone()[0])
