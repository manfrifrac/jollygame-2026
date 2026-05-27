import pandas as pd
import json
from collections import Counter

def check_duplicates():
    # 1. Analyze Excel Listino
    print("--- Analisi Excel (LISTINOMANUFACTURASGRE2026.xlsx) ---")
    excel_file = 'LISTINOMANUFACTURASGRE2026.xlsx'
    df = pd.read_excel(excel_file)
    
    excel_skus = []
    excel_eans = []
    
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else None
        ean = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else None
        
        if sku and sku not in ['NAN', 'REF', 'ARTICOLO'] and len(sku) > 2:
            excel_skus.append(sku)
        if ean and ean not in ['NAN', 'EAN', ''] and len(ean) > 5:
            excel_eans.append(ean)

    sku_counts_excel = Counter(excel_skus)
    ean_counts_excel = Counter(excel_eans)
    
    dup_skus_excel = {sku: count for sku, count in sku_counts_excel.items() if count > 1}
    dup_eans_excel = {ean: count for ean, count in ean_counts_excel.items() if count > 1}
    
    print(f"SKU Duplicati in Excel: {len(dup_skus_excel)}")
    for sku, count in dup_skus_excel.items():
        print(f"  - SKU {sku}: presente {count} volte")
        
    print(f"EAN Duplicati in Excel: {len(dup_eans_excel)}")
    for ean, count in dup_eans_excel.items():
        print(f"  - EAN {ean}: presente {count} volte")

    # 2. Analyze Shopify Data
    print("\n--- Analisi Shopify (shopify_gre_full_data.json) ---")
    with open('shopify_gre_full_data.json', 'r') as f:
        shopify_data = json.load(f)
        
    shopify_skus = []
    shopify_variants = {} # SKU -> [Product Title]
    
    for p in shopify_data:
        for v in p['variants']:
            sku = str(v['sku']).strip().upper() if v['sku'] else None
            if sku and sku != 'NONE':
                shopify_skus.append(sku)
                if sku not in shopify_variants: shopify_variants[sku] = []
                shopify_variants[sku].append(p['title'])

    sku_counts_shopify = Counter(shopify_skus)
    dup_skus_shopify = {sku: count for sku, count in sku_counts_shopify.items() if count > 1}
    
    print(f"SKU Duplicati su Shopify: {len(dup_skus_shopify)}")
    for sku, count in dup_skus_shopify.items():
        products = ", ".join(set(shopify_variants[sku]))
        print(f"  - SKU {sku}: presente {count} volte nei prodotti: [{products}]")

    # 3. Cross-Check
    print("\n--- Sintesi ---")
    print(f"Totale SKU univoci in Excel: {len(sku_counts_excel)}")
    print(f"Totale SKU univoci su Shopify: {len(sku_counts_shopify)}")

if __name__ == "__main__":
    check_duplicates()
