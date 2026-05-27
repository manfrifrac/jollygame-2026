import pandas as pd
import json
import os

def audit_gre_variants():
    # 1. Load Excel
    listino_path = "LISTINOMANUFACTURASGRE2026.xlsx"
    df = pd.read_excel(listino_path, header=2)
    listino_skus = set(df['ARTICOLO'].dropna().astype(str).str.strip().str.upper())
    
    # 2. Load Shopify Data
    shopify_path = "jollygame-importer/jollygame-importer/master_catalog_dump.json"
    with open(shopify_path, 'r', encoding='utf-8') as f:
        shopify_products = json.load(f)

    shopify_gre_skus = set()
    for p in shopify_products:
        if p.get('vendor') == 'Gre':
            for v in p['variants']['nodes']:
                sku = v.get('sku')
                if sku:
                    shopify_gre_skus.add(sku.strip().upper())

    missing = listino_skus - shopify_gre_skus
    extra = shopify_gre_skus - listino_skus

    print(f"📊 AUDIT VARIANTI GRE:")
    print(f"✅ SKUs nel Listino: {len(listino_skus)}")
    print(f"✅ SKUs Gre su Shopify: {len(shopify_gre_skus)}")
    print(f"❌ SKUs Mancanti su Shopify: {len(missing)}")
    print(f"❓ SKUs Extra su Shopify (non in listino): {len(extra)}")

    if len(missing) > 0:
        print("\n🔎 ESEMPI DI VARIANTI/PRODOTTI MANCANTI:")
        # Trova titoli per questi SKU dall'Excel
        missing_details = df[df['ARTICOLO'].astype(str).str.strip().str.upper().isin(missing)]
        for _, row in missing_details.head(15).iterrows():
            print(f" - {row['ARTICOLO']}: {row['DESCRIZIONE']}")

    if len(extra) > 0:
        print("\n🔎 ESEMPI DI VARIANTI EXTRA (da controllare se obsoleti):")
        for sku in list(extra)[:10]:
            print(f" - {sku}")

if __name__ == "__main__":
    audit_gre_variants()
