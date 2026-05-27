import sqlite3

def check_10201():
    conn = sqlite3.connect("intex_catalog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, source, title, url FROM products WHERE sku = '10201'")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_10201()
