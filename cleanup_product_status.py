import pandas as pd
import requests
import os
from dotenv import dotenv_values

# Load Shopify credentials
env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)

SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def get_gre_skus_from_excel(file_path):
    print(f"Reading Gre SKUs from {file_path}...")
    df = pd.read_excel(file_path)
    # SKU is column 6 (Index 6)
    skus = set()
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else None
        if sku and sku != 'NAN' and sku != 'REF' and len(sku) > 2:
            skus.add(sku)
    return skus

def get_all_shopify_products():
    products = []
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    
    cursor = None
    has_next_page = True
    
    print("Fetching Shopify products...")
    while has_next_page:
        query = """
        query($cursor: String) {
          products(first: 250, after: $cursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                id
                title
                vendor
                status
                variants(first: 10) {
                  edges {
                    node {
                      sku
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {"cursor": cursor}
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        data = response.json()
        
        if 'errors' in data:
            print("Error:", data['errors'])
            break
            
        edges = data['data']['products']['edges']
        for edge in edges:
            node = edge['node']
            skus = [v['node']['sku'].strip().upper() for v in node['variants']['edges'] if v['node']['sku']]
            products.append({
                "id": node['id'],
                "title": node['title'],
                "vendor": node['vendor'],
                "status": node['status'],
                "skus": skus
            })
            
        page_info = data['data']['products']['pageInfo']
        has_next_page = page_info['hasNextPage']
        cursor = page_info['endCursor']
        
    return products

def update_product_status(product_id, status):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    
    query = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product {
          id
          status
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
            "status": status
        }
    }
    
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return response.json()

def main():
    excel_file = 'LISTINOMANUFACTURASGRE2026.xlsx'
    gre_skus = get_gre_skus_from_excel(excel_file)
    print(f"Total Gre SKUs in listino: {len(gre_skus)}")
    
    shopify_products = get_all_shopify_products()
    print(f"Total products on Shopify: {len(shopify_products)}")
    
    to_draft = []
    to_active = []
    
    for p in shopify_products:
        is_gre = (p['vendor'] == 'Gre')
        in_listino = any(sku in gre_skus for sku in p['skus'])
        
        # Logic:
        # - If NOT Gre -> DRAFT
        # - If Gre AND in Listino -> ACTIVE
        # - If Gre AND NOT in Listino -> DRAFT
        
        target_status = 'DRAFT'
        if is_gre and in_listino:
            target_status = 'ACTIVE'
        
        if p['status'] != target_status:
            if target_status == 'DRAFT':
                to_draft.append(p)
            else:
                to_active.append(p)

    print(f"\nPlan:")
    print(f"Move to DRAFT: {len(to_draft)}")
    print(f"Move to ACTIVE: {len(to_active)}")
    
    # Execute updates
    print("\nUpdating statuses...")
    for p in to_draft:
        print(f"DRAFTing: {p['title']} ({p['vendor']})")
        res = update_product_status(p['id'], 'DRAFT')
        if 'errors' in res or (res.get('data') and res['data']['productUpdate']['userErrors']):
            print(f"Error updating {p['title']}: {res}")

    for p in to_active:
        print(f"ACTIVATING: {p['title']} ({p['vendor']})")
        res = update_product_status(p['id'], 'ACTIVE')
        if 'errors' in res or (res.get('data') and res['data']['productUpdate']['userErrors']):
            print(f"Error updating {p['title']}: {res}")

    print("\nCleanup completed.")

if __name__ == "__main__":
    main()
