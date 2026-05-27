import sqlite3
import re
import json

def check_data_cleanliness():
    conn = sqlite3.connect('bestway_catalog.db')
    cursor = conn.cursor()

    print("="*50)
    print("   CONTROLLO PULIZIA DATI BESTWAY   ")
    print("="*50)

    cursor.execute("SELECT sku, ean, title, price, description_html, images FROM bestway_products")
    rows = cursor.fetchall()

    issues = {
        "sku_with_junk": [],
        "ean_invalid": [],
        "title_with_html": [],
        "price_invalid": [],
        "desc_with_css_junk": [],
        "empty_images": []
    }

    for row in rows:
        sku, ean, title, price, desc, images = row
        
        # 1. Check SKU for CSS/JS junk (e.g. curly braces)
        if sku and ("{" in sku or "}" in sku or "<" in sku):
            issues["sku_with_junk"].append(sku)
            
        # 2. Check EAN for non-numeric characters (allow empty)
        if ean:
            clean_ean = re.sub(r'[^0-9]', '', str(ean))
            if clean_ean != str(ean):
                issues["ean_invalid"].append((sku, ean))
                
        # 3. Check Title for HTML tags
        if title and re.search(r'<[^>]+>', title):
            issues["title_with_html"].append((sku, title))
            
        # 4. Check Price
        if price is not None:
            try:
                p = float(price)
                if p <= 0:
                    issues["price_invalid"].append((sku, price))
            except ValueError:
                issues["price_invalid"].append((sku, price))
        
        # 5. Check Description for CSS junk (like ".loadingDots")
        if desc and (".loadingDots" in desc or "display: flex" in desc or "{" in desc):
            # Sometimes inline CSS has {}, but usually product descriptions shouldn't have raw CSS blocks
            # We'll do a loose check for common junk we saw earlier
            if re.search(r'\.[a-zA-Z0-9_-]+\s*\{', desc):
                issues["desc_with_css_junk"].append(sku)
                
        # 6. Check Images
        if not images or len(images.strip()) == 0:
            issues["empty_images"].append(sku)

    # Report
    print(f"\nRisultati dell'analisi su {len(rows)} prodotti:")
    
    print(f"\n1. SKU con caratteri sporchi (CSS/HTML): {len(issues['sku_with_junk'])}")
    if issues['sku_with_junk']:
        for s in issues['sku_with_junk'][:5]: print(f"   - {s}")
            
    print(f"\n2. EAN con caratteri non numerici: {len(issues['ean_invalid'])}")
    if issues['ean_invalid']:
        for s, e in issues['ean_invalid'][:5]: print(f"   - [{s}] EAN: {e}")
            
    print(f"\n3. Titoli con tag HTML: {len(issues['title_with_html'])}")
    if issues['title_with_html']:
        for s, t in issues['title_with_html'][:5]: print(f"   - [{s}] {t}")
            
    print(f"\n4. Prezzi invalidi o a zero: {len(issues['price_invalid'])}")
    if issues['price_invalid']:
        for s, p in issues['price_invalid'][:5]: print(f"   - [{s}] Prezzo: {p}")
            
    print(f"\n5. Descrizioni con codice CSS/JS sospetto: {len(issues['desc_with_css_junk'])}")
    if issues['desc_with_css_junk']:
        for s in issues['desc_with_css_junk'][:5]: print(f"   - [{s}]")
            
    print(f"\n6. Prodotti senza immagini: {len(issues['empty_images'])}")
    if issues['empty_images']:
        for s in issues['empty_images'][:5]: print(f"   - [{s}]")

    print("\n" + "="*50)
    conn.close()

if __name__ == "__main__":
    check_data_cleanliness()
