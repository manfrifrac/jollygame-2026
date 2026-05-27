
import json
import pandas as pd
import requests
import os
import dotenv

# Load environment variables
dotenv.load_dotenv('jollygame-importer/jollygame-importer/.env')

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_URL = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"

def run_query(query, variables=None):
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=headers)
    return response.json()

def update_handle(product_id, new_handle):
    mutation = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id handle }
        userErrors { field message }
      }
    }
    """
    return run_query(mutation, {"input": {"id": product_id, "handle": new_handle}})

def create_redirect(old_path, target_path):
    mutation = """
    mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
      urlRedirectCreate(urlRedirect: $urlRedirect) {
        urlRedirect { id }
        userErrors { field message }
      }
    }
    """
    return run_query(mutation, {"urlRedirect": {"path": old_path, "target": target_path}})

def align_pattern_based():
    # Load Shopify Gre products
    shopify_file = 'jollygame-importer/jollygame-importer/shopify_gre_products.json'
    with open(shopify_file, 'r', encoding='utf-8') as f:
        shopify_products = json.load(f)
    
    sku_to_product = {}
    for p in shopify_products:
        for v in p['variants']['nodes']:
            if v['sku']:
                sku_to_product[v['sku'].strip().upper()] = p

    # List of SKUs from Grepool mapping that we want to align
    # Pattern: /category/sku-slug.html -> handle: sku-slug
    # Based on Sumatra and manual inspection of how PrestaShop (old site) worked
    
    # We'll use the mapping CSV to get the list of SKUs and try to "find" their handles
    # Since we can't scrape all reliably, we'll use a safer approach:
    # Only update if we are SURE.
    
    # But wait, the user wants them to work.
    # Let's try to find if we have any other source for the old handles.
    
    # Actually, I'll check 'mapping_completo_PER_LAVORO_MANUALE.csv' for Redirect_From_DA_INCOLLARE again.
    manual_df = pd.read_csv('mapping_completo_PER_LAVORO_MANUALE.csv')
    valid_redirects = manual_df[manual_df['Redirect_From_DA_INCOLLARE'].notna()]
    
    print(f"Found {len(valid_redirects)} valid redirects in manual mapping.")
    
    for _, row in valid_redirects.iterrows():
        sku = str(row['SKU']).strip().upper()
        old_path = row['Redirect_From_DA_INCOLLARE']
        
        # old_path looks like /category/sku-slug.html
        new_handle = old_path.split("/")[-1].replace(".html", "")
        
        p = sku_to_product.get(sku)
        if not p:
            print(f"SKU {sku} not found on Shopify.")
            continue
            
        print(f"🚀 Aligning {sku}...")
        
        # 1. Update Handle
        res_h = update_handle(p['id'], new_handle)
        if res_h.get('data', {}).get('productUpdate', {}).get('userErrors'):
            print(f"  [ERROR] Handle: {res_h['data']['productUpdate']['userErrors']}")
        else:
            print(f"  [OK] Handle set to: {new_handle}")
            
        # 2. Create Redirect
        res_r = create_redirect(old_path, f"/products/{new_handle}")
        if res_r.get('data', {}).get('urlRedirectCreate', {}).get('userErrors'):
            err = res_r['data']['urlRedirectCreate']['userErrors']
            if any("taken" in e['message'].lower() for e in err):
                print(f"  [INFO] Redirect exists.")
            else:
                print(f"  [ERROR] Redirect: {err}")
        else:
            print(f"  [OK] Redirect created.")

if __name__ == "__main__":
    align_pattern_based()
