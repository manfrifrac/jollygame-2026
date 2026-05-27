import pandas as pd
import json
import os

def exhaustive_gre_audit():
    # 1. Load Excel
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
    df['SKU_CLEAN'] = df['ARTICOLO'].astype(str).str.strip().str.upper()
    
    # 2. Load Shopify
    with open('jollygame-importer/jollygame-importer/master_catalog_dump.json', 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    shopify_skus = {}
    for p in catalog:
        if p.get('vendor') == 'Gre':
            for v in p['variants']['nodes']:
                sku = (v.get('sku') or "").strip().upper()
                if sku:
                    shopify_skus[sku] = {
                        "product_title": p['title'],
                        "price": v['price'],
                        "status": p['status']
                    }

    # 3. Analyze Excel
    results = []
    for _, row in df.iterrows():
        sku = row['SKU_CLEAN']
        if not sku or sku == 'NAN': continue
        
        price = row['PREZZO DI VENDITA CONSIGLIATO 2026']
        on_shopify = sku in shopify_skus
        
        results.append({
            "sku": sku,
            "title": row['DESCRIZIONE'],
            "price_in_listino": price,
            "on_shopify": on_shopify,
            "shopify_status": shopify_skus[sku]['status'] if on_shopify else "N/A",
            "category": row['CATEGORIA 3']
        })

    res_df = pd.DataFrame(results)
    
    print("📊 AUDIT DETTAGLIATO VARIANTI GRE:")
    print(f"📦 Totale SKUs nel Listino: {len(res_df)}")
    print(f"✅ SKUs presenti su Shopify: {res_df['on_shopify'].sum()}")
    print(f"❌ SKUs mancanti su Shopify: {len(res_df) - res_df['on_shopify'].sum()}")
    
    print("\n🔍 Analisi dei mancanti:")
    missing = res_df[~res_df['on_shopify']]
    missing_with_price = missing[missing['price_in_listino'].notna()]
    missing_no_price = missing[missing['price_in_listino'].isna()]
    
    print(f"   - Mancanti MA con prezzo (DA IMPORTARE): {len(missing_with_price)}")
    print(f"   - Mancanti SENZA prezzo (Saltati): {len(missing_no_price)}")

    if len(missing_with_price) > 0:
        print("\n🚀 VARIANTI CON PREZZO DA AGGIUNGERE SUBITO:")
        for _, row in missing_with_price.head(10).iterrows():
            print(f" - {row['sku']}: {row['title']} ({row['price_in_listino']} €)")

    # 4. Check for grouped variants
    print("\n👨‍👩‍👧‍👦 Controllo Famiglie Prodotti (es. Piscine con più taglie):")
    # Group by category and common title parts
    families = res_df.groupby('category').size().sort_values(ascending=False).head(10)
    print("Top categorie nel listino:")
    print(families)

if __name__ == "__main__":
    exhaustive_gre_audit()
