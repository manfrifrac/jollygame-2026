import sqlite3

conn = sqlite3.connect('fluidra_clean.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT p.sku, p.title, p.images_json, pr.parent_sku 
    FROM products p 
    JOIN product_relations pr ON p.sku = pr.child_sku 
    WHERE p.images_json != '[]' AND p.images_json != '' AND p.images_json IS NOT NULL
    LIMIT 10;
''')
ricambi = cursor.fetchall()

for r in ricambi:
    print(r)
