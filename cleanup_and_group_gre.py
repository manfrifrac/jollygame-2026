import json
import requests
import os
import re
from collections import defaultdict
from dotenv import dotenv_values

# Load Shopify credentials
env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)
SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def query_shopify(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    res = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return res.json()

def get_clean_group_name(title, subcat):
    t = title.upper().replace('KIT ', '').replace('PISCINA ', '').replace('PER ', '').replace('IN ', '').replace('COP.', '').replace('COPERTURA ', '')
    name = t.split()[0]
    return f"{subcat} | {name}"

def delete_product(pid):
    q = "mutation($input: ProductDeleteInput!) { productDelete(input: $input) { deletedProductId } }"
    query_shopify(q, {"input": {"id": pid}})

def main():
    # 1. Load Master Listino
    with open('listino_master_map.json', 'r') as f:
        listino = json.load(f)
    
    # Define Master Groups
    master_groups = defaultdict(list)
    sku_to_group = {}
    for sku, info in listino.items():
        g_name = get_clean_group_name(info['title'], info['subcategory'])
        master_groups[g_name].append(sku)
        sku_to_group[sku] = g_name

    # 2. Get current Shopify data
    # (Using the script from before to refresh)
    os.system("python get_shopify_gre_full.py")
    with open('shopify_gre_full_data.json', 'r') as f:
        shopify_data = json.load(f)

    # Map Shopify Products to Groups
    group_to_shopify_prods = defaultdict(list)
    for p in shopify_data:
        # Find which group this product belongs to based on its variants' SKUs
        p_groups = set()
        for v in p['variants']:
            sku = str(v['sku']).strip().upper() if v['sku'] else None
            if sku in sku_to_group:
                p_groups.add(sku_to_group[sku])
        
        if p_groups:
            # Most products should only belong to one group
            # If a product has variants from multiple groups, it's a "messy" product
            main_group = list(p_groups)[0]
            group_to_shopify_prods[main_group].append(p)
        else:
            # Product with no valid SKUs - should have been deleted already but let's be safe
            print(f"Product {p['title']} has no valid SKUs. Consider deleting.")

    # 3. Process Merges
    for g_name, prods in group_to_shopify_prods.items():
        if len(prods) > 1:
            print(f"Merging group: {g_name} ({len(prods)} products)")
            # Keep the one with the most variants or marked as ACTIVE
            prods.sort(key=lambda x: (x['status'] == 'ACTIVE', len(x['variants'])), reverse=True)
            master_prod = prods[0]
            others = prods[1:]
            
            for other in others:
                print(f"  Deleting redundant product: {other['title']}")
                delete_product(other['id'])

    print("\nMerge and cleanup complete.")

if __name__ == "__main__":
    main()
