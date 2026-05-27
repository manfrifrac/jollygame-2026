import json
import requests
import os
import re
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

def get_variant_name(title):
    match = re.search(r'Dim:?\s*(.*)$', title, re.IGNORECASE)
    if match: return match.group(1).strip()
    if ' - ' in title: return title.split(' - ', 1)[1].strip()
    # If title is too long, truncate it
    if len(title) > 50: return title[:47] + "..."
    return title

def main():
    with open('gre_reimport_plan.json', 'r') as f:
        plan = json.load(f)
    
    with open('listino_master_map.json', 'r') as f:
        listino = json.load(f)

    # 1. Refresh current Shopify products to avoid ID conflicts
    os.system("python get_shopify_gre_full.py")
    with open('shopify_gre_full_data.json', 'r') as f:
        shopify_data = json.load(f)
    
    # Map group name to existing Shopify Product ID
    existing_prods = {}
    for p in shopify_data:
        # Check variants to identify which group it likely belongs to
        for v in p['variants']:
            sku = str(v['sku']).strip().upper()
            if sku in listino:
                # Find the group name for this SKU
                t = listino[sku]['title'].upper().replace('KIT ', '').replace('PISCINA ', '').replace('PER ', '').replace('IN ', '').replace('COP.', '').replace('COPERTURA ', '')
                name = t.split()[0]
                group_name = f"{listino[sku]['subcategory']} | {name}"
                existing_prods[group_name] = p['id']
                break

    print(f"Starting Re-import of {len(plan)} groups...")

    for group_name, skus in plan.items():
        print(f"Processing group: {group_name}")
        
        product_id = existing_prods.get(group_name)
        
        # Prepare variants and collect all unique option values
        variants_input = []
        option_values_seen = set()
        
        for sku in skus:
            info = listino[sku]
            val_name = get_variant_name(info['title'])
            
            # If name is duplicate within this product, append SKU to make it unique
            if val_name in option_values_seen:
                val_name = f"{val_name} ({sku})"
            
            option_values_seen.add(val_name)
            
            variants_input.append({
                "price": str(info['price']) if str(info['price']) != 'nan' else "0",
                "barcode": info['ean'],
                "inventoryItem": {
                    "sku": sku
                },
                "optionValues": [
                    {
                        "name": val_name,
                        "optionName": "Modello o Misura"
                    }
                ]
            })

        # Construct ProductSet input
        input_obj = {
            "title": f"Gre - {group_name.split(' | ')[1]} ({group_name.split(' | ')[0]})",
            "vendor": "Gre",
            "productType": group_name.split(' | ')[0],
            "status": "DRAFT",
            "productOptions": [
                {
                    "name": "Modello o Misura",
                    "values": [{"name": val} for val in option_values_seen]
                }
            ],
            "variants": variants_input
        }
        
        if product_id:
            input_obj["id"] = product_id

        # Execute productSet
        query = """
        mutation productSet($input: ProductSetInput!) {
          productSet(input: $input) {
            product { id title }
            userErrors { field message }
          }
        }
        """
        res = query_shopify(query, {"input": input_obj})
        
        if 'errors' in res or (res.get('data') and res['data']['productSet']['userErrors']):
            print(f"  ❌ Error: {res}")
        else:
            p_res = res['data']['productSet']['product']
            print(f"  ✅ Successfully synced: {p_res['title']} (ID: {p_res['id']})")

    print("\nRe-import and restructuring complete.")

if __name__ == "__main__":
    main()
