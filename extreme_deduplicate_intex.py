import sqlite3

def deduplicate_final():
    conn = sqlite3.connect("intex_catalog.db")
    cursor = conn.cursor()

    # Get all duplicate SKUs
    cursor.execute("SELECT sku FROM products WHERE sku != '' GROUP BY sku HAVING COUNT(*) > 1")
    duplicate_skus = [r[0] for r in cursor.fetchall()]

    print(f"Deduplicating {len(duplicate_skus)} SKUs...")

    for sku in duplicate_skus:
        cursor.execute("SELECT id, source, short_description FROM products WHERE sku = ?", (sku,))
        instances = cursor.fetchall()
        
        # Priority: intex_italia (usually better content)
        instances.sort(key=lambda x: (0 if x[1] == 'intex_italia' else 1, -len(x[2] or "")))
        
        master_id = instances[0][0]
        duplicate_ids = [i[0] for i in instances[1:]]
        
        # 1. Update spare_parts to point to master_id
        for dup_id in duplicate_ids:
            cursor.execute("UPDATE spare_parts SET product_id = ? WHERE product_id = ?", (master_id, dup_id))
            # 2. Delete the duplicate product
            cursor.execute("DELETE FROM products WHERE id = ?", (dup_id,))

    conn.commit()
    conn.close()
    print("Deduplication complete.")

if __name__ == "__main__":
    deduplicate_final()
