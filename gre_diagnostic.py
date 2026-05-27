import json
import pandas as pd
from collections import Counter

def diagnostic():
    with open('shopify_gre_full_data.json', 'r') as f:
        data = json.load(f)
    
    listino_df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx')
    listino_skus = {} # SKU -> {ean, price, title}
    for _, row in listino_df.iterrows():
        sku = str(row.iloc[6]).strip().upper()
        if sku and sku not in ['NAN', 'REF', 'ARTICOLO']:
            listino_skus[sku] = {
                "ean": str(row.iloc[9]).strip(),
                "price": row.iloc[15],
                "title": str(row.iloc[7]).strip()
            }

    all_skus = []
    all_eans = []
    strange_items = []
    
    sku_to_products = {} # SKU -> list of product titles

    print(f"Analyzing {len(data)} Gre products on Shopify...\n")

    for p in data:
        p_title = p['title']
        variants = p['variants']
        
        v_skus = [v['sku'].strip().upper() for v in variants if v['sku']]
        v_sku_counts = Counter(v_skus)
        
        # 1. Duplicate SKUs within same product
        for sku, count in v_sku_counts.items():
            if count > 1:
                strange_items.append(f"[!] SKU DUPLICATO INTERNO: '{sku}' in '{p_title}' ({count} volte)")

        for v in variants:
            sku = str(v['sku']).strip().upper() if v['sku'] else None
            
            # 2. Missing SKU
            if not sku or sku == 'NONE':
                strange_items.append(f"[?] SKU MANCANTE: Variante '{v['title']}' in '{p_title}'")
                continue
            
            all_skus.append(sku)
            if sku not in sku_to_products: sku_to_products[sku] = []
            sku_to_products[sku].append(p_title)

            # 3. Check against Listino
            if sku in listino_skus:
                l_data = listino_skus[sku]
                # Price check (approximate due to potential formatting)
                # (Skipping for now as user asked specifically about duplicates/variants)
                pass
            else:
                strange_items.append(f"[i] SKU NON IN LISTINO 2026: '{sku}' in '{p_title}'")

            # 4. Option naming check
            for opt_name, opt_val in v['options'].items():
                if sku in str(opt_val):
                    strange_items.append(f"[-] OPZIONE STRANA: '{opt_name}'='{opt_val}' contiene lo SKU in '{p_title}'")

            # 5. Image check
            if not v['image']:
                strange_items.append(f"[x] IMMAGINE MANCANTE: SKU '{sku}' in '{p_title}'")

    # 6. Global Duplicate Check (Cross-Product)
    sku_counts_global = Counter(all_skus)
    for sku, count in sku_counts_global.items():
        if count > 1:
            prods = ", ".join(set(sku_to_products[sku]))
            strange_items.append(f"[!!] SKU DUPLICATO GLOBALE: '{sku}' in prodotti diversi: [{prods}]")

    # Print results
    if not strange_items:
        print("Nessuna anomalia rilevata.")
    else:
        # Group by category for readability
        for item in sorted(strange_items):
            print(item)

if __name__ == "__main__":
    diagnostic()
