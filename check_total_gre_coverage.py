import json
import requests
import os
from dotenv import dotenv_values

env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)
SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def query_shopify(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    res = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return res.json()

def main():
    # 1. Check all vendors
    v_query = "{ productVendors(first: 100) { edges { node } } }"
    v_res = query_shopify(v_query)
    vendors = [e['node'] for e in v_res['data']['productVendors']['edges']]
    print(f"Vendors on Shopify: {vendors}")

    # 2. Check for Gre in title but different vendor
    t_query = """
    query {
      products(first: 250, query: "title:*Gre* -vendor:Gre") {
        edges {
          node {
            title
            vendor
          }
        }
      }
    }
    """
    t_res = query_shopify(t_query)
    other_gre = [e['node'] for e in t_res['data']['products']['edges']]
    print(f"\nProducts with 'Gre' in title but NOT 'Gre' as vendor: {len(other_gre)}")
    for p in other_gre:
        print(f"  - {p['title']} (Vendor: {p['vendor']})")

    # 3. Check SKU coverage
    with open('listino_master_map.json', 'r') as f:
        listino = json.load(f)
    listino_skus = set(listino.keys())

    # Fetch ALL Shopify SKUs (not just Gre)
    all_shopify_skus = set()
    cursor = None
    has_next_page = True
    while has_next_page:
        s_query = """
        query($cursor: String) {
          products(first: 250, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            edges {
              node {
                variants(first: 100) {
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
        s_res = query_shopify(s_query, {"cursor": cursor})
        for edge in s_res['data']['products']['edges']:
            for v_edge in edge['node']['variants']['edges']:
                sku = v_edge['node']['sku']
                if sku: all_shopify_skus.add(sku.strip().upper())
        
        has_next_page = s_res['data']['products']['pageInfo']['hasNextPage']
        cursor = s_res['data']['products']['pageInfo']['endCursor']

    missing_skus = listino_skus - all_shopify_skus
    print(f"\nSKU Coverage Summary:")
    print(f"Total unique SKUs in 2026 Listino: {len(listino_skus)}")
    print(f"Total unique SKUs found on Shopify (any vendor): {len(all_shopify_skus)}")
    print(f"Listino SKUs NOT on Shopify: {len(missing_skus)}")

if __name__ == "__main__":
    main()
