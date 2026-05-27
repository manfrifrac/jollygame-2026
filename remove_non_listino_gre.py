import json
import requests
import os
from dotenv import dotenv_values

# Load Shopify credentials
env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)

SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def delete_product(product_id):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    query = """
    mutation productDelete($input: ProductDeleteInput!) {
      productDelete(input: $input) {
        deletedProductId
        userErrors { field message }
      }
    }
    """
    variables = {"input": {"id": product_id}}
    res = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return res.json()

def main():
    with open('shopify_gre_to_clean.json', 'r') as f:
        data = json.load(f)
    
    to_remove = data['remove']
    print(f"Removing {len(to_remove)} products not found in Listino 2026...")
    
    for p in to_remove:
        print(f"Deleting: {p['title']} (ID: {p['id']})")
        res = delete_product(p['id'])
        if 'errors' in res or (res.get('data') and res['data']['productDelete']['userErrors']):
            print(f"  Error: {res}")
            
    print("Cleanup of non-listino products complete.")

if __name__ == "__main__":
    main()
