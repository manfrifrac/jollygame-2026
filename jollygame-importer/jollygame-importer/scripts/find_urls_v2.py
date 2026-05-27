import pandas as pd
import json
import os

def find_urls_by_sku():
    new_products_path = "new_gre_products_to_import.json"
    mapping_path = "../../mapping_prodotti_jolly_gre_FINALE.csv"
    
    if not os.path.exists(new_products_path) or not os.path.exists(mapping_path):
        print(f"File non trovati: new_products={os.path.exists(new_products_path)}, mapping={os.path.exists(mapping_path)}")
        return

    with open(new_products_path, 'r', encoding='utf-8') as f:
        new_products = json.load(f)

    # Load Mapping
    df_map = pd.read_csv(mapping_path)
    
    # Create map SKU -> URL
    sku_to_url = {}
    for _, row in df_map.iterrows():
        sku = str(row['SKU']).strip().upper()
        url = str(row['Grepool_URL'])
        if sku and url and url != 'nan':
            sku_to_url[sku] = url

    found_count = 0
    for p in new_products:
        p_sku = str(p['sku']).strip().upper()
        if p_sku in sku_to_url:
            p['gre_url'] = sku_to_url[p_sku]
            found_count += 1

    print(f"✅ Trovati {found_count} URL via SKU Match nel mapping file.")
    
    with open("new_gre_products_with_urls.json", "w", encoding="utf-8") as f:
        json.dump(new_products, f, indent=2)

if __name__ == "__main__":
    find_urls_by_sku()
