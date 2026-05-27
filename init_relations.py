import sqlite3

def init_relations():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    
    # Crea tabella relazioni
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_relations (
        parent_sku TEXT,
        child_sku TEXT,
        relation_type TEXT,
        PRIMARY KEY (parent_sku, child_sku, relation_type)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Tabella product_relations creata/verificata.")

if __name__ == "__main__":
    init_relations()
