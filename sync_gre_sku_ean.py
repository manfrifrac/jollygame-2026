import json
import requests
import os
from dotenv import dotenv_values

# Load Shopify credentials
env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)

SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def update_variants_bulk(product_id, variants_input):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    query = """
    mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
      productVariantsBulkUpdate(productId: $productId, variants: $variants) {
        product { id }
        productVariants { id sku barcode price }
        userErrors { field message }
      }
    }
    """
    variables = {
        "productId": product_id,
        "variants": variants_input
    }
    res = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return res.json()

def main():
    with open('shopify_gre_to_clean.json', 'r') as f:
        data = json.load(f)
    
    with open('listino_master_map.json', 'r') as f:
        listino_map = json.load(f)
        
    keep_products = data['keep']
    print(f"Synchronizing SKU/EAN for {len(keep_products)} products...")
    
    for p in keep_products:
        print(f"Checking variants for: {p['title']}")
        variants_to_update = []
        for v in p['variants']:
            sku = str(v['sku']).strip().upper() if v['sku'] else None
            if sku in listino_map:
                info = listino_map[sku]
                variants_to_update.append({
                    "id": v['id'],
                    "barcode": info['ean'],
                    "price": str(info['price']),
                    "inventoryItem": {
                        "sku": sku
                    }
                })
        
        if variants_to_update:
            print(f"  Updating {len(variants_to_update)} variants in bulk for {p['title']}...")
            res = update_variants_bulk(p['id'], variants_to_update)
            if 'errors' in res or (res.get('data') and res['data']['productVariantsBulkUpdate']['userErrors']):
                print(f"    Error: {res}")
            else:
                print(f"    ✅ Successfully updated variants.")

if __name__ == "__main__":
    main()
