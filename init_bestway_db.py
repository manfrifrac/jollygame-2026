import sqlite3

def init_db():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bestway_products (
        sku TEXT PRIMARY KEY,
        ean TEXT,
        title TEXT,
        price REAL,
        description_html TEXT,
        bullet_points TEXT,
        category TEXT,
        images TEXT,
        video TEXT,
        url TEXT,
        specs_json TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database bestway_catalog.db inizializzato correttamente.")

if __name__ == "__main__":
    init_db()
