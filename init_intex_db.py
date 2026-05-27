import sqlite3
import json
import os

def create_database():
    if not os.path.exists("intex_full_catalog.json"):
        print("Error: intex_full_catalog.json not found.")
        return

    with open("intex_full_catalog.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect("intex_catalog.db")
    cursor = conn.cursor()

    # Create Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        url TEXT UNIQUE,
        title TEXT,
        sku TEXT,
        short_description TEXT,
        description TEXT,
        images TEXT -- Stored as JSON string
    )
    ''')

    # Create Spare Parts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS spare_parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        ref TEXT,
        sku TEXT,
        name TEXT,
        price TEXT,
        stock TEXT,
        url TEXT,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')

    print("Inserting data into database...")
    for item in data:
        try:
            # Insert product
            cursor.execute('''
            INSERT OR REPLACE INTO products (source, url, title, sku, short_description, description, images)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get("source"),
                item.get("url"),
                item.get("title"),
                item.get("sku"),
                item.get("short_description", ""),
                item.get("description", ""),
                json.dumps(item.get("images", []))
            ))
            
            product_id = cursor.lastrowid

            # Insert spare parts
            for spare in item.get("spare_parts", []):
                cursor.execute('''
                INSERT INTO spare_parts (product_id, ref, sku, name, price, stock, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_id,
                    spare.get("ref", ""),
                    spare.get("sku", ""),
                    spare.get("name", ""),
                    spare.get("price", ""),
                    spare.get("stock", ""),
                    spare.get("url", "")
                ))
        except Exception as e:
            print(f"Error inserting {item.get('url')}: {e}")

    conn.commit()
    conn.close()
    print("Database 'intex_catalog.db' created and populated successfully.")

if __name__ == "__main__":
    create_database()
