
import dotenv
import os
import json
import requests

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

def update_handle(product_id, new_handle):
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
    variables = {
        "input": {
            "id": product_id,
            "handle": new_handle
        }
    }
    return run_query(mutation, variables)

def create_redirect(old_path, new_path):
    mutation = """
    mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
      urlRedirectCreate(urlRedirect: $urlRedirect) {
        urlRedirect {
          id
          path
          target
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {
        "urlRedirect": {
            "path": old_path,
            "target": new_path
        }
    }
    return run_query(mutation, variables)

if __name__ == "__main__":
    # POC: Update Sumatra Ovale
    sumatra_sku = "KPEOV5027"
    # From full_source_rendered.html
    old_full_url = "https://www.jollygame.it/piscine-interrate/kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120.html"
    old_path = "/piscine-interrate/kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120.html"
    new_slug = "kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120"
    
    # 1. Find product on Shopify
    query = f'{{ products(first: 1, query: "sku:{sumatra_sku}") {{ nodes {{ id handle }} }} }}'
    res = run_query(query)
    products = res['data']['products']['nodes']
    
    if products:
        p = products[0]
        p_id = p['id']
        old_handle = p['handle']
        
        print(f"Product found: {p_id}")
        print(f"Current handle: {old_handle}")
        print(f"New handle suggested: {new_slug}")
        
        # 2. Update Handle
        # update_res = update_handle(p_id, new_slug)
        # print(f"Update result: {update_res}")
        
        # 3. Create Redirect
        # target_path = f"/products/{new_slug}"
        # redir_res = create_redirect(old_path, target_path)
        # print(f"Redirect result: {redir_res}")
        
        print("\n--- ACTION REQUIRED ---")
        print(f"To align with Gre's site, we should:")
        print(f"1. Change handle to: {new_slug}")
        print(f"2. Create redirect from: {old_path} to: /products/{new_slug}")
    else:
        print(f"Product with SKU {sumatra_sku} not found on Shopify.")
