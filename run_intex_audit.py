import sqlite3
import json

def run_audit():
    conn = sqlite3.connect("intex_catalog.db")
    cursor = conn.cursor()

    # Total counts
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT source, COUNT(*) FROM products GROUP BY source")
    source_counts = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM spare_parts")
    total_spares = cursor.fetchone()[0]

    # Cleanliness metrics
    cursor.execute("SELECT COUNT(*) FROM products WHERE sku IS NULL OR sku = ''")
    missing_sku = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE images = '[]'")
    missing_images = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE source = 'intex_italia' AND (description = '' AND short_description = '')")
    missing_desc_italia = cursor.fetchone()[0]

    # Duplicate check
    cursor.execute("SELECT sku, COUNT(*) as c FROM products WHERE sku != '' GROUP BY sku HAVING c > 1")
    duplicate_skus = cursor.fetchall()

    cursor.execute("SELECT title, COUNT(*) as c FROM products GROUP BY title HAVING c > 1")
    duplicate_titles = cursor.fetchall()

    # Category Audit (Inferred from URL)
    cursor.execute("SELECT url FROM products")
    urls = [r[0] for r in cursor.fetchall()]
    categories = {}
    for url in urls:
        parts = url.strip("/").split("/")
        # For Intex Italia: domain/cat/subcat/product or domain/cat/product
        # For Intex Ricambi: domain/ricambi/product
        if "intexitalia.com" in url:
            if len(parts) > 3:
                cat = parts[3] # Usually the category slug
            else:
                cat = "root"
        elif "intexricambi.it" in url:
            cat = "ricambi"
        else:
            cat = "unknown"
        
        categories[cat] = categories.get(cat, 0) + 1

    # Spare Parts Stats
    cursor.execute("SELECT COUNT(DISTINCT product_id) FROM spare_parts")
    products_with_spares = cursor.fetchone()[0]

    conn.close()

    print("--- 🎯 INTEX CATALOG AUDIT ---")
    print(f"Total Unique Products: {total_products}")
    print(f"  - Intex Italia: {source_counts.get('intex_italia', 0)}")
    print(f"  - Intex Ricambi: {source_counts.get('intex_ricambi', 0)}")
    print(f"Total Spare Parts linked: {total_spares}")
    print(f"Products with a dedicated spare parts list: {products_with_spares}")

    print("\n--- 🧹 CLEANLINESS & COMPLETENESS ---")
    print(f"Products missing SKU: {missing_sku} ({(missing_sku/total_products)*100:.1f}%)")
    print(f"Products missing Images: {missing_images}")
    print(f"Italia products missing description: {missing_desc_italia}")
    print(f"Duplicate SKUs found: {len(duplicate_skus)}")
    print(f"Duplicate Titles found: {len(duplicate_titles)}")

    print("\n--- 📂 CATEGORY DISTRIBUTION (Slug based) ---")
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    for cat, count in sorted_cats:
        print(f"  - {cat}: {count}")

if __name__ == "__main__":
    run_audit()
