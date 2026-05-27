
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

def apply_confirmed_alignments():
    # Load Shopify products to get IDs
    shopify_file = 'jollygame-importer/jollygame-importer/shopify_gre_products.json'
    with open(shopify_file, 'r', encoding='utf-8') as f:
        shopify_products = json.load(f)
    
    sku_to_id = {}
    for p in shopify_products:
        for v in p['variants']['nodes']:
            if v['sku']:
                sku_to_id[v['sku'].strip().upper()] = p['id']

    # Confirmed alignments from research
    alignments = [
        {
            "sku": "KPEOV5027",
            "old_path": "/piscine-interrate/kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120.html",
            "new_handle": "kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120"
        },
        {
            "sku": "790000",
            "old_path": "/piscina-quadrata-in-legno-gre-city-225x225x65-cm-790000.html",
            "new_handle": "piscina-quadrata-in-legno-gre-city-225x225x65-cm-790000"
        },
        {
            "sku": "790207",
            "old_path": "/piscine-gre-montaggio-prezzi-fuoriterra-alta-dimensioni-rotonda-ovale-costo-prezzo-giardino-bassa/piscina-fuori-terra-in-legno-rettangolare-braga-790207-gre-sunbay-travi-metalliche-pino.html",
            "new_handle": "piscina-fuori-terra-in-legno-rettangolare-braga-790207-gre-sunbay-travi-metalliche-pino"
        },
        {
            "sku": "790206",
            "old_path": "/piscina-fuori-terra-in-legno-rettangolare-evora-790206-gre-sunbay-travi-metalliche-pino.html",
            "new_handle": "piscina-fuori-terra-in-legno-rettangolare-evora-790206-gre-sunbay-travi-metalliche-pino"
        }
    ]

    for al in alignments:
        p_id = sku_to_id.get(al['sku'])
        if not p_id:
            print(f"SKU {al['sku']} not found on Shopify.")
            continue
            
        print(f"🚀 Aligning {al['sku']}...")
        
        # 1. Update Handle
        res_h = update_handle(p_id, al['new_handle'])
        if res_h.get('data', {}).get('productUpdate', {}).get('userErrors'):
            print(f"  [ERROR] Handle: {res_h['data']['productUpdate']['userErrors']}")
        else:
            print(f"  [OK] Handle updated.")
            
        # 2. Create Redirect
        target = f"/products/{al['new_handle']}"
        res_r = create_redirect(al['old_path'], target)
        if res_r.get('data', {}).get('urlRedirectCreate', {}).get('userErrors'):
            err = res_r['data']['urlRedirectCreate']['userErrors']
            if any("taken" in e['message'].lower() for e in err):
                print(f"  [INFO] Redirect already exists.")
            else:
                print(f"  [ERROR] Redirect: {err}")
        else:
            print(f"  [OK] Redirect created.")

if __name__ == "__main__":
    apply_confirmed_alignments()
