import sqlite3

def find_anomalies():
    conn = sqlite3.connect("intex_catalog.db")
    cursor = conn.cursor()

    print("--- 🔍 PRODOTTI SENZA SKU ---")
    cursor.execute("SELECT id, source, url, title FROM products WHERE sku IS NULL OR sku = ''")
    for row in cursor.fetchall():
        print(row)

    print("\n--- 🔍 SKU DUPLICATI ---")
    cursor.execute("SELECT sku, COUNT(*) as c FROM products WHERE sku != '' GROUP BY sku HAVING c > 1")
    for row in cursor.fetchall():
        print(row)

    print("\n--- 🔍 TITOLI DUPLICATI ---")
    cursor.execute("SELECT title, COUNT(*) as c FROM products GROUP BY title HAVING c > 1")
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    find_anomalies()
