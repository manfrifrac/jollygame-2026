
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
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=headers)
    return response.json()

def update_product_handle(product_id, new_handle):
    mutation = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product {
          id
          handle
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {"input": {"id": product_id, "handle": new_handle}}
    return run_query(mutation, variables)

def create_url_redirect(old_path, target_path):
    mutation = """
    mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
      urlRedirectCreate(urlRedirect: $urlRedirect) {
        urlRedirect {
          id
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {"urlRedirect": {"path": old_path, "target": target_path}}
    return run_query(mutation, variables)

def apply_alignment():
    results_file = "gre_alignment_results.csv"
    if not os.path.exists(results_file):
        print(f"Error: {results_file} not found. Run scraper first.")
        return
    
    df = pd.read_csv(results_file)
    # Filter for products where we found a suggested handle
    to_align = df[df['Suggested_Handle'].notna()]
    
    if to_align.empty:
        print("No products found to align yet.")
        return
    
    print(f"Found {len(to_align)} products to align.")
    
    # Load current Shopify products for mapping
    shopify_file = 'jollygame-importer/jollygame-importer/shopify_gre_products.json'
    if not os.path.exists(shopify_file):
        print("Shopify products file not found.")
        return
    
    with open(shopify_file, 'r', encoding='utf-8') as f:
        shopify_products = json.load(f)
    
    sku_to_id = {}
    for p in shopify_products:
        for v in p['variants']['nodes']:
            if v['sku']:
                sku_to_id[v['sku'].strip().upper()] = p['id']

    for index, row in to_align.iterrows():
        sku = str(row['SKU']).strip().upper()
        new_handle = row['Suggested_Handle']
        old_path = row['Old_Path']
        
        p_id = sku_to_id.get(sku)
        if not p_id:
            print(f"SKU {sku} not found on Shopify.")
            continue
            
        print(f"Aligning {sku}: New Handle -> {new_handle}, Redirect -> {old_path}")
        
        # 1. Update Handle
        upd_res = update_product_handle(p_id, new_handle)
        if upd_res.get('data', {}).get('productUpdate', {}).get('userErrors'):
            print(f"  [ERROR] Update failed for {sku}: {upd_res['data']['productUpdate']['userErrors']}")
        else:
            print(f"  [SUCCESS] Handle updated.")
            
        # 2. Create Redirect
        target = f"/products/{new_handle}"
        redir_res = create_url_redirect(old_path, target)
        if redir_res.get('data', {}).get('urlRedirectCreate', {}).get('userErrors'):
            errors = redir_res['data']['urlRedirectCreate']['userErrors']
            # Ignore "Path has already been taken" error
            if any("taken" in e['message'].lower() for e in errors):
                print(f"  [INFO] Redirect already exists.")
            else:
                print(f"  [ERROR] Redirect failed for {sku}: {errors}")
        else:
            print(f"  [SUCCESS] Redirect created.")

if __name__ == "__main__":
    apply_alignment()
