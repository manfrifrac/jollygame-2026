
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

def apply_updates():
    # 1. Load manual data or found data
    # We found Sumatra as a proof:
    updates = [
        {
            "sku": "KPEOV5027",
            "old_path": "/piscine-interrate/kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120.html",
            "new_handle": "kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120"
        }
    ]
    
    # Check if we have more in gre_handle_alignment_map.csv
    if os.path.exists("gre_handle_alignment_map.csv"):
        df = pd.read_csv("gre_handle_alignment_map.csv")
        found = df[df['Suggested_Handle'].notna()]
        for _, row in found.iterrows():
            if row['SKU'] != "KPEOV5027": # Avoid duplicate
                updates.append({
                    "sku": row['SKU'],
                    "old_path": row['Old_Path'],
                    "new_handle": row['Suggested_Handle']
                })

    if not updates:
        print("No updates to apply yet.")
        return

    # Load Shopify products to get IDs
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

    for up in updates:
        p_id = sku_to_id.get(up['sku'])
        if not p_id:
            print(f"SKU {up['sku']} not found on Shopify.")
            continue
            
        print(f"🚀 Aligning {up['sku']}...")
        
        # Update Handle
        res_h = update_handle(p_id, up['new_handle'])
        if res_h.get('data', {}).get('productUpdate', {}).get('userErrors'):
            print(f"  [ERROR] Handle update: {res_h['data']['productUpdate']['userErrors']}")
        else:
            print(f"  [OK] Handle: {up['new_handle']}")
            
        # Create Redirect
        res_r = create_redirect(up['old_path'], f"/products/{up['new_handle']}")
        if res_r.get('data', {}).get('urlRedirectCreate', {}).get('userErrors'):
            err = res_r['data']['urlRedirectCreate']['userErrors']
            if any("taken" in e['message'].lower() for e in err):
                print(f"  [INFO] Redirect already exists.")
            else:
                print(f"  [ERROR] Redirect: {err}")
        else:
            print(f"  [OK] Redirect created.")

if __name__ == "__main__":
    apply_updates()
