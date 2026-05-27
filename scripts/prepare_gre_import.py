import sqlite3
import json
import os

def prepare_new_products():
    report_path = "gre_price_update_report.json"
    if not os.path.exists(report_path):
        print("Report non trovato.")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    # 186 products in listino but not on shopify
    missing = report['missing_on_shopify']
    
    # DB Connections
    fluidra_conn = sqlite3.connect('fluidra_catalog.db')
    f_cursor = fluidra_conn.cursor()

    bestway_conn = sqlite3.connect('bestway_catalog.db')
    b_cursor = bestway_conn.cursor()

    new_products_data = []

    for item in missing:
        sku = item['sku']
        ean = item.get('ean')
        price = item['price']
        
        # Search in Fluidra
        f_cursor.execute("SELECT title, description, images_json, taxonomy, specs_json FROM products WHERE sku = ?", (sku,))
        row = f_cursor.fetchone()
        
        if row:
            new_products_data.append({
                "sku": sku,
                "ean": ean,
                "title": row[0],
                "description": row[1],
                "images": json.loads(row[2]) if row[2] else [],
                "taxonomy": row[3],
                "specs": json.loads(row[4]) if row[4] else {},
                "price": price,
                "vendor": "Gre"
            })
        else:
            # Placeholder for products with no DB info
            new_products_data.append({
                "sku": sku,
                "ean": ean,
                "title": item['title'],
                "description": "Prodotto originale Gre. Qualità e durata garantite.",
                "images": [],
                "taxonomy": "Gre",
                "specs": {},
                "price": price,
                "vendor": "Gre"
            })

    fluidra_conn.close()
    bestway_conn.close()

    with open("new_gre_products_to_import.json", "w", encoding="utf-8") as f:
        json.dump(new_products_data, f, indent=2)

    print(f"✅ Preparati {len(new_products_data)} prodotti per l'importazione.")
    found = len([p for p in new_products_data if p['description'] != "Prodotto originale Gre. Qualità e durata garantite."])
    print(f"✨ Dati completi trovati nel DB per {found} prodotti.")

if __name__ == "__main__":
    prepare_new_products()
