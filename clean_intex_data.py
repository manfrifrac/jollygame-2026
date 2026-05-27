import sqlite3
import re
import json

def clean_and_update():
    conn = sqlite3.connect("intex_catalog.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, source, url, title, sku, short_description FROM products")
    products = cursor.fetchall()

    print("Starting data cleaning and SKU extraction...")
    
    updated_count = 0
    for p_id, source, url, title, sku, short_desc in products:
        new_sku = sku
        new_title = title

        # 1. Extract SKU if missing
        if not new_sku or new_sku == "":
            # Try from title (e.g. "Piscina ... 28101NP")
            sku_match = re.search(r'(\d{5}[A-Z]{0,2})', title)
            if sku_match:
                new_sku = sku_match.group(1)
            else:
                # Try from URL (e.g. "...-28101np/")
                sku_match = re.search(r'-(\d{5}[a-z]{0,2})/?$', url.strip("/"))
                if sku_match:
                    new_sku = sku_match.group(1).upper()

        # 2. Fix Missing Titles (mostly Intex Italia)
        if not new_title or new_title == "":
            # Try to get first line of short description or from URL slug
            if short_desc:
                # Get first sentence or first 50 chars
                first_line = short_desc.split(".")[0].strip()
                if len(first_line) > 10:
                    new_title = first_line
            
            if not new_title or new_title == "":
                # From URL slug: /altalene-swing-set/altalena-colorata.../
                slug = url.strip("/").split("/")[-1]
                new_title = slug.replace("-", " ").capitalize()

        if new_sku != sku or new_title != title:
            cursor.execute("UPDATE products SET sku = ?, title = ? WHERE id = ?", (new_sku, new_title, p_id))
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"Update complete. {updated_count} products updated with extracted SKUs or Titles.")

if __name__ == "__main__":
    clean_and_update()
