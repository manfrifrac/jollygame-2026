import pandas as pd
import requests
import os
from dotenv import dotenv_values

env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)
SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def get_gre_skus_from_excel(file_path):
    df = pd.read_excel(file_path)
    skus = set()
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else None
        if sku and sku != 'NAN' and sku != 'REF' and len(sku) > 2:
            skus.add(sku)
    return skus

def get_shopify_gre_products():
    products = []
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    cursor = None
    has_next_page = True
    while has_next_page:
        query = """
        query($cursor: String) {
          products(first: 250, query: "vendor:Gre", after: $cursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
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
        edges = data['data']['products']['edges']
        for edge in edges:
            node = edge['node']
            skus = [v['node']['sku'].strip().upper() for v in node['variants']['edges'] if v['node']['sku']]
            products.append({"status": node['status'], "skus": skus})
        page_info = data['data']['products']['pageInfo']
        has_next_page = page_info['hasNextPage']
        cursor = page_info['endCursor']
    return products

excel_file = 'LISTINOMANUFACTURASGRE2026.xlsx'
excel_skus = get_gre_skus_from_excel(excel_file)
shopify_gre = get_shopify_gre_products()

published_skus = set()
draft_skus = set()

for p in shopify_gre:
    for sku in p['skus']:
        if sku in excel_skus:
            if p['status'] == 'ACTIVE':
                published_skus.add(sku)
            else:
                draft_skus.add(sku)

missing_skus = excel_skus - published_skus - draft_skus

print(f"SKU totali nel listino Gre: {len(excel_skus)}")
print(f"SKU Gre pubblicati (ACTIVE): {len(published_skus)}")
print(f"SKU Gre presenti ma in bozza (DRAFT): {len(draft_skus)}")
print(f"SKU Gre del listino NON ANCORA CARICATI: {len(missing_skus)}")
