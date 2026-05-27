import sqlite3

conn = sqlite3.connect('fluidra_clean.db')
cursor = conn.cursor()

# Cerchiamo un prodotto che ha un diagram_url popolato
cursor.execute("SELECT sku, title, diagram_url FROM products WHERE diagram_url IS NOT NULL AND diagram_url != '' LIMIT 5;")
esplosi = cursor.fetchall()

print("--- Esempio Esplosi ---")
for e in esplosi:
    print(e)
    # Cerchiamo i ricambi collegati a questo SKU (padre) tramite product_relations
    cursor.execute("SELECT child_sku, diagram_index FROM product_relations WHERE parent_sku = ?", (e[0],))
    ricambi = cursor.fetchall()
    print("Ricambi collegati:", ricambi)
    print("---")
