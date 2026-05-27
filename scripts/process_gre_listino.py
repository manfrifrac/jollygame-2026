import pandas as pd
import json
import os

def process_listino():
    # 1. Load Excel
    listino_path = "LISTINOMANUFACTURASGRE2026.xlsx"
    df = pd.read_excel(listino_path, header=2)
    
    # 2. Load Shopify Data
    shopify_path = "jollygame-importer/jollygame-importer/master_catalog_dump.json"
    with open(shopify_path, 'r', encoding='utf-8') as f:
        shopify_products = json.load(f)

    # Convert Shopify variants to a map for fast lookup
    shopify_variants = {}
    for p in shopify_products:
        for v in p['variants']['nodes']:
            if v['sku']:
                shopify_variants[v['sku'].strip().upper()] = {
                    "product_id": p['id'],
                    "variant_id": v['id'],
                    "title": p['title'],
                    "current_price": v['price'],
                    "status": p['status']
                }

    updates = []
    missing_on_shopify = []
    
    # 3. Iterate through Excel
    for _, row in df.iterrows():
        sku = str(row['ARTICOLO']).strip().upper()
        if not sku or sku == 'NAN': continue
        
        raw_price = row['PREZZO DI VENDITA CONSIGLIATO 2026']
        if pd.isna(raw_price): continue
        
        # Calculate 3% markup
        try:
            price_val = float(raw_price)
            # Round to 2 decimals
            final_price = round(price_val * 1.03, 2)
        except:
            continue

        if sku in shopify_variants:
            v = shopify_variants[sku]
            updates.append({
                "sku": sku,
                "product_id": v['product_id'],
                "variant_id": v['variant_id'],
                "title": v['title'],
                "old_price": v['current_price'],
                "new_price": str(final_price),
                "status": v['status']
            })
        else:
            missing_on_shopify.append({
                "sku": sku,
                "ean": str(int(row['EAN'])) if pd.notna(row['EAN']) else None,
                "title": row['DESCRIZIONE'],
                "price": final_price
            })

    # 4. Check for products on Shopify but not in Listino (Gre only)
    listino_skus = set([str(s).strip().upper() for s in df['ARTICOLO'] if pd.notna(s)])
    missing_in_listino = []
    for sku, v in shopify_variants.items():
        # Only check Gre products
        # We can detect Gre from title or if we know which ones they are.
        # Let's just list all not in listino.
        if sku not in listino_skus:
            missing_in_listino.append({
                "sku": sku,
                "title": v['title']
            })

    # Save results
    report = {
        "summary": {
            "total_in_listino": len(df),
            "matched_to_update": len(updates),
            "missing_on_shopify": len(missing_on_shopify),
            "on_shopify_not_in_listino": len(missing_in_listino)
        },
        "updates": updates,
        "missing_on_shopify": missing_on_shopify,
        "on_shopify_not_in_listino": missing_in_listino
    }

    with open("gre_price_update_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"📊 REPORT GENERATO:")
    print(f"✅ Prodotti da aggiornare: {len(updates)}")
    print(f"⚠️  Prodotti nel listino ma non su Shopify: {len(missing_on_shopify)}")
    print(f"❓ Prodotti su Shopify ma non nel listino: {len(missing_in_listino)}")

if __name__ == "__main__":
    process_listino()
