import pandas as pd
import requests
import os
from dotenv import dotenv_values

# Load Shopify credentials
env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)

SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def get_all_shopify_products():
    products = []
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    
    cursor = None
    has_next_page = True
    
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
                title
                vendor
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
            print("Error fetching Shopify products:", data['errors'])
            break
            
        edges = data['data']['products']['edges']
        for edge in edges:
            node = edge['node']
            skus = [v['node']['sku'].strip().upper() for v in node['variants']['edges'] if v['node']['sku']]
            products.append({
                "title": node['title'],
                "vendor": node['vendor'],
                "skus": skus
            })
            
        page_info = data['data']['products']['pageInfo']
        has_next_page = page_info['hasNextPage']
        cursor = page_info['endCursor']
        
    return products

def get_excel_products(file_path):
    df = pd.read_excel(file_path)
    excel_products = []
    
    # Based on our inspection:
    # SKU is column 6 (Index 6)
    # Title is column 7 (Index 7)
    # EAN is column 9 (Index 9)
    # Price is column 15 (Index 15)
    
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else None
        title = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else None
        
        if sku and sku != 'NAN' and sku != 'REF' and len(sku) > 2:
            excel_products.append({
                "sku": sku,
                "title": title
            })
            
    return excel_products

def main():
    excel_file = 'LISTINOMANUFACTURASGRE2026.xlsx'
    print(f"Reading Excel: {excel_file}...")
    excel_products = get_excel_products(excel_file)
    excel_skus = {p['sku']: p['title'] for p in excel_products}
    
    print(f"Fetching Shopify products...")
    shopify_products = get_all_shopify_products()
    shopify_skus = {} # SKU -> Title
    for p in shopify_products:
        for sku in p['skus']:
            shopify_skus[sku] = p['title']
            
    missing = []
    for sku, title in excel_skus.items():
        if sku not in shopify_skus:
            missing.append({"sku": sku, "title": title})
            
    print(f"\nResults:")
    print(f"Total products in Excel: {len(excel_products)}")
    print(f"Total unique SKUs in Excel: {len(excel_skus)}")
    print(f"Total products on Shopify: {len(shopify_products)}")
    print(f"Total unique SKUs on Shopify: {len(shopify_skus)}")
    
    print(f"\nMissing on Shopify: {len(missing)}")
    
    if missing:
        print("\nFirst 50 missing products:")
        for i, p in enumerate(missing[:50]):
            print(f"{i+1}. {p['sku']} - {p['title']}")
            
        # Save to CSV for the user
        missing_df = pd.DataFrame(missing)
        missing_df.to_csv('prodotti_gre_mancanti.csv', index=False)
        print(f"\nComplete list saved to prodotti_gre_mancanti.csv")

if __name__ == "__main__":
    main()
