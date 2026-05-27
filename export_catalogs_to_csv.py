import sqlite3
import csv
import json
import os

def export_to_csv(db_path, table_name, output_file, mapping):
    if not os.path.exists(db_path):
        print(f"Skipping {db_path}, not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all columns from table
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [c[1] for c in cursor.fetchall()]
    
    # Select all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Titolo", "Prezzo", "SKU", "EAN", "Tags", 
            "Descrizione_HTML", "Caratteristiche_Tecniche", "Immagini_JSON"
        ])
        writer.writeheader()
        
        for row in rows:
            record = dict(zip(cols, row))
            
            # Basic mapping
            out = {
                "Titolo": record.get(mapping['title'], ""),
                "Prezzo": record.get(mapping['price'], "0.00"),
                "SKU": record.get(mapping['sku'], ""),
                "EAN": record.get(mapping['ean'], ""),
                "Descrizione_HTML": record.get(mapping['desc'], ""),
                "Caratteristiche_Tecniche": record.get(mapping['specs'], ""),
                "Immagini_JSON": record.get(mapping['images'], "[]"),
            }
            
            # Category to Tags
            tags = []
            raw_cat = record.get(mapping['category'], "")
            if raw_cat:
                if isinstance(raw_cat, str):
                    tags.append(raw_cat)
                elif isinstance(raw_cat, list):
                    tags.extend(raw_cat)
            
            if record.get('is_spare_part') == 1:
                tags.append("Ricambio")
            
            out["Tags"] = ",".join(tags)
            writer.writerow(out)
            
    conn.close()
    print(f"Exported {output_file}")

# 1. Intex
export_to_csv(
    "intex_clean.db", "products", "intex_export_shopify.csv",
    {
        "title": "title", "price": "price", "sku": "sku", "ean": "ean",
        "desc": "short_description", "specs": "attributes", "images": "images", "category": "categories"
    }
)

# 2. Bestway
export_to_csv(
    "bestway_clean.db", "bestway_products", "bestway_export_shopify.csv",
    {
        "title": "title", "price": "price", "sku": "sku", "ean": "ean",
        "desc": "description_html", "specs": "bullet_points", "images": "images", "category": "category"
    }
)

# 3. Fluidra (Surgical selection - first 1000 to keep it manageable or filter by is_spare_part)
export_to_csv(
    "fluidra_clean.db", "products", "fluidra_export_shopify.csv",
    {
        "title": "title", "price": "price_list", "sku": "sku", "ean": "ean",
        "desc": "description", "specs": "specs_json", "images": "images_json", "category": "taxonomy"
    }
)
