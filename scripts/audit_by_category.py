import pandas as pd
import json
import os

def audit_by_category():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx', header=2)
    df['SKU_CLEAN'] = df['ARTICOLO'].astype(str).str.strip().str.upper()
    
    with open('jollygame-importer/jollygame-importer/master_catalog_dump.json', 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    shopify_skus = set()
    for p in catalog:
        if p.get('vendor') == 'Gre':
            for v in p['variants']['nodes']:
                sku = (v.get('sku') or "").strip().upper()
                if sku: shopify_skus.add(sku)

    df['on_shopify'] = df['SKU_CLEAN'].isin(shopify_skus)
    
    # Group by CATEGORIA 3
    summary = df.groupby('CATEGORIA 3').agg({
        'SKU_CLEAN': 'count',
        'on_shopify': 'sum'
    }).rename(columns={'SKU_CLEAN': 'Total in Listino', 'on_shopify': 'Found on Shopify'})
    
    summary['Missing'] = summary['Total in Listino'] - summary['Found on Shopify']
    summary = summary.sort_values('Missing', ascending=False)
    
    print("📊 AUDIT COPERTURA VARIANTI PER CATEGORIA:")
    print(summary.to_string())

    # Check for missing pools specifically
    pool_cats = [c for c in summary.index if any(x in str(c).lower() for x in ['piscine', 'acciaio', 'legno', 'composito'])]
    if pool_cats:
        print("\n🔎 DETTAGLIO PISCINE MANCANTI:")
        missing_pools = df[(df['CATEGORIA 3'].isin(pool_cats)) & (~df['on_shopify']) & (df['PREZZO DI VENDITA CONSIGLIATO 2026'].notna())]
        if not missing_pools.empty:
            for _, row in missing_pools.iterrows():
                print(f" - [{row['CATEGORIA 3']}] {row['ARTICOLO']}: {row['DESCRIZIONE']}")
        else:
            print(" ✅ Tutte le piscine con prezzo nel listino sono presenti su Shopify.")

if __name__ == "__main__":
    audit_by_category()
