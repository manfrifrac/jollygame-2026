import sqlite3
import os

db_path = "fluidra_clean.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Cerco SKU che iniziano con KIT (tipico di Gre) o altri codici comuni Gre
cursor.execute("SELECT sku, title FROM products WHERE sku LIKE 'KIT%' OR sku LIKE '7%' OR sku LIKE 'P%' LIMIT 20")
results = cursor.fetchall()

print(f"Esempi di SKU trovati nel DB Fluidra:")
for r in results:
    print(f"  {r}")

cursor.execute("SELECT COUNT(*) FROM products WHERE sku LIKE 'KIT%'")
print(f"\nTotale SKU KIT: {cursor.fetchone()[0]}")

conn.close()
