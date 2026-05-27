import sqlite3
import json

def clean_database():
    conn = sqlite3.connect('intex_deep_catalog.db')
    cursor = conn.cursor()
    
    # 1. Count initial rows
    cursor.execute("SELECT COUNT(*) FROM products")
    initial_count = cursor.fetchone()[0]
    print(f"=== INIZIO PULIZIA DATABASE ===")
    print(f"Prodotti iniziali: {initial_count}")
    
    # 2. Fix HTML entities like &amp; in title and short_description
    cursor.execute("UPDATE products SET title = REPLACE(title, '&amp;', '&') WHERE title LIKE '%&amp;%'")
    cursor.execute("UPDATE products SET short_description = REPLACE(short_description, '&amp;', '&') WHERE short_description LIKE '%&amp;%'")
    conn.commit()
    print("Corrette entità HTML (&amp; -> &).")

    # 3. Deduplication strategy based on SKU
    # Many products exist in both intexitalia.com and intexricambi.it.
    # We want to keep the one that has more data (e.g., EAN, Price, Images).
    
    cursor.execute("SELECT sku, COUNT(*) FROM products WHERE sku != '' GROUP BY sku HAVING COUNT(*) > 1")
    duplicate_skus = cursor.fetchall()
    print(f"\nTrovati {len(duplicate_skus)} SKU duplicati.")
    
    removed_count = 0
    updated_count = 0
    
    for sku_row in duplicate_skus:
        sku = sku_row[0]
        # Fetch all records for this SKU
        cursor.execute("SELECT rowid, url, ean, price, images, pdfs, attributes FROM products WHERE sku = ?", (sku,))
        records = cursor.fetchall()
        
        # Determine the "best" record to keep
        # Score based on: has EAN (+10), has price (+5), has images (+ len(images)), has pdfs (+ len(pdfs))
        best_record_id = None
        best_score = -1
        best_data = {}
        
        for record in records:
            rowid, url, ean, price, images_json, pdfs_json, attrs_json = record
            score = 0
            if ean: score += 10
            if price: score += 5
            
            try:
                images = json.loads(images_json)
                score += len(images)
            except: images = []
            
            try:
                pdfs = json.loads(pdfs_json)
                score += len(pdfs)
            except: pdfs = []
            
            if score > best_score:
                best_score = score
                best_record_id = rowid
                best_data = {
                    'ean': ean,
                    'price': price,
                    'images': images_json,
                    'pdfs': pdfs_json,
                    'attributes': attrs_json
                }
            elif score == best_score:
                # Tie-breaker: Prefer intexitalia.com over intexricambi.it if possible
                if "intexitalia.com" in url:
                    best_record_id = rowid
                    best_data = {
                        'ean': ean,
                        'price': price,
                        'images': images_json,
                        'pdfs': pdfs_json,
                        'attributes': attrs_json
                    }
        
        # Merge missing data into the best record from other records before deleting them
        merged_ean = best_data['ean']
        merged_price = best_data['price']
        
        for record in records:
            rowid, url, ean, price, images_json, pdfs_json, attrs_json = record
            if rowid != best_record_id:
                if not merged_ean and ean: merged_ean = ean
                if not merged_price and price: merged_price = price
                # We could merge images/pdfs but usually they are the same or one is better.
                # Let's keep it simple for now and just merge EAN/Price.
                
                # Delete the duplicate
                cursor.execute("DELETE FROM products WHERE rowid = ?", (rowid,))
                removed_count += 1
        
        # Update the best record with merged data if anything changed
        if merged_ean != best_data['ean'] or merged_price != best_data['price']:
            cursor.execute("UPDATE products SET ean = ?, price = ? WHERE rowid = ?", (merged_ean, merged_price, best_record_id))
            updated_count += 1

    conn.commit()
    
    # 4. Check for EAN duplicates (different SKUs but same EAN)
    cursor.execute("SELECT ean, COUNT(*) FROM products WHERE ean != '' GROUP BY ean HAVING COUNT(*) > 1")
    duplicate_eans = cursor.fetchall()
    print(f"Trovati {len(duplicate_eans)} EAN duplicati (con SKU diversi).")
    # Usually this means it's the same product sold as a bundle or a slight variant.
    # We will log them but not automatically delete, as they might be legitimate variants (e.g. pool with vs without pump).
    for ean_row in duplicate_eans:
        ean = ean_row[0]
        cursor.execute("SELECT sku, title FROM products WHERE ean = ?", (ean,))
        print(f"  - EAN {ean} condiviso da:")
        for r in cursor.fetchall():
            print(f"    * SKU: {r[0]} | {r[1][:50]}...")
            
    # 5. Final count
    cursor.execute("SELECT COUNT(*) FROM products")
    final_count = cursor.fetchone()[0]
    
    print(f"\n=== RISULTATI PULIZIA ===")
    print(f"Prodotti rimossi (duplicati esatti di SKU): {removed_count}")
    print(f"Prodotti aggiornati (unione dati): {updated_count}")
    print(f"Prodotti finali nel database: {final_count}")
    
    conn.close()

if __name__ == '__main__':
    clean_database()
