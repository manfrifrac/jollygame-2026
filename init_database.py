import sqlite3
import json

def init_db():
    conn = sqlite3.connect('fluidra_catalog.db')
    cursor = conn.cursor()

    # Tabella Prodotti (Main + Spares)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            sku TEXT PRIMARY KEY,
            ean TEXT,
            title TEXT,
            description TEXT,
            price_net REAL,
            price_list REAL,
            discount TEXT,
            stock_italy INTEGER,
            stock_spain INTEGER,
            taxonomy TEXT,
            images_json TEXT,
            docs_json TEXT,
            videos_json TEXT,
            specs_json TEXT,
            url TEXT,
            is_spare_part INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabella Relazioni (Padre -> Figlio)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_relations (
            parent_sku TEXT,
            child_sku TEXT,
            diagram_index TEXT,
            PRIMARY KEY (parent_sku, child_sku),
            FOREIGN KEY (parent_sku) REFERENCES products(sku),
            FOREIGN KEY (child_sku) REFERENCES products(sku)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database SQLite inizializzato correttamente.")

if __name__ == "__main__":
    init_db()
