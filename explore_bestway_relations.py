import sqlite3
import json

def explore_relations():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()
    
    # Cerchiamo prodotti che non siano ricambi (pezzi principali)
    # e analizziamo il loro JSON per chiavi come 'related', 'compatible', 'parts'
    cursor.execute("SELECT sku, title, specs_json FROM bestway_products WHERE sku NOT LIKE 'P%' LIMIT 20")
    rows = cursor.fetchall()
    
    print("=== ESPLORAZIONE RELAZIONI PRODOTTO ===")
    
    for sku, title, specs_raw in rows:
        specs = json.loads(specs_raw)
        
        # Cerchiamo chiavi interessanti
        relation_keys = [k for k in specs.keys() if any(x in k.lower() for x in ['related', 'part', 'compat', 'accessory', 'bom'])]
        
        if relation_keys:
            print(f"\nProdotto: [{sku}] {title}")
            for k in relation_keys:
                val = specs[k]
                print(f"  - Chiave '{k}': {val}")
        
    conn.close()

if __name__ == "__main__":
    explore_relations()
