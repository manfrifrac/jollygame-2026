import sqlite3

conn = sqlite3.connect('bestway_catalog.db')
cursor = conn.cursor()
cursor.execute('SELECT sku, url FROM bestway_products WHERE title LIKE "%Pompa%" AND title LIKE "%Sabbia%" LIMIT 5')
for r in cursor.fetchall():
    print(f"{r[0]}: {r[1]}")
conn.close()
