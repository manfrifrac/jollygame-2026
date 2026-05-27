import pandas as pd
import requests
import json
import os
from dotenv import dotenv_values
from difflib import SequenceMatcher

# Load Shopify credentials
env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)

SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_listino_map():
    df = pd.read_excel('LISTINOMANUFACTURASGRE2026.xlsx')
    mapping = {}
    for _, row in df.iterrows():
        sku = str(row.iloc[6]).strip().upper()
        if sku and sku not in ['NAN', 'REF', 'ARTICOLO']:
            mapping[sku] = str(row.iloc[7]).strip()
    return mapping

def get_all_gre_shopify():
    products = []
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    cursor = None
    has_next_page = True
    while has_next_page:
        query = """
        query($cursor: String) {
          products(first: 250, query: "vendor:Gre", after: $cursor) {
            pageInfo { hasNextPage endCursor }
            edges {
              node {
                id
                title
                status
                variants(first: 100) {
                  edges {
                    node {
                      id
                      sku
                    }
                  }
                }
              }
            }
          }
        }
        """
        response = requests.post(url, json={"query": query, "variables": {"cursor": cursor}}, headers=headers)
        data = response.json()
        if "errors" in data: break
        edges = data["data"]["products"]["edges"]
        for edge in edges:
            products.append(edge["node"])
        has_next_page = data["data"]["products"]["pageInfo"]["hasNextPage"]
        cursor = data["data"]["products"]["pageInfo"]["endCursor"]
    return products

def delete_variant(variant_id):
    # Actually, you can't delete the only variant of a product easily, 
    # but you can delete the whole product if it's redundant.
    # For this cleanup, if we find a duplicate variant in a different product, 
    # we usually want to delete the redundant product.
    pass

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
    requests.post(url, json={"query": query, "variables": variables}, headers=headers)

def main():
    listino = get_listino_map()
    print(f"Loaded {len(listino)} SKUs from Listino.")
    
    shopify_products = get_all_gre_shopify()
    print(f"Found {len(shopify_products)} Gre products on Shopify.")
    
    sku_map = {} # SKU -> list of {prod_id, variant_id, prod_title, status}
    
    for p in shopify_products:
        for v in p['variants']['edges']:
            vn = v['node']
            sku = str(vn['sku']).strip().upper() if vn['sku'] else None
            if not sku or sku == 'NONE': continue
            
            if sku not in sku_map: sku_map[sku] = []
            sku_map[sku].append({
                "prod_id": p['id'],
                "variant_id": vn['id'],
                "prod_title": p['title'],
                "status": p['status']
            })
            
    to_delete_product_ids = set()
    
    for sku, occurrences in sku_map.items():
        if len(occurrences) > 1:
            print(f"\nDuplicate found for SKU: {sku}")
            
            # Decide which to keep
            listino_title = listino.get(sku, "")
            
            best_match = None
            max_score = -1
            
            for occ in occurrences:
                # Score based on status (ACTIVE > DRAFT) and title similarity
                score = 0
                if occ['status'] == 'ACTIVE': score += 10
                
                sim = similarity(occ['prod_title'], listino_title)
                score += sim * 5
                
                occ['temp_score'] = score
                if score > max_score:
                    max_score = score
                    best_match = occ
            
            print(f"  KEEPING: {best_match['prod_title']} (Score: {best_match['temp_score']:.2f})")
            
            for occ in occurrences:
                if occ != best_match:
                    print(f"  REMOVING: {occ['prod_title']} (Score: {occ['temp_score']:.2f})")
                    to_delete_product_ids.add(occ['prod_id'])

    print(f"\nTotal unique products to delete: {len(to_delete_product_ids)}")
    
    if to_delete_product_ids:
        # confirmed = input("Proceed with deletion? (y/n): ")
        # if confirmed.lower() == 'y':
        for pid in to_delete_product_ids:
            print(f"Deleting product {pid}...")
            delete_product(pid)
        print("Cleanup completed.")
    else:
        print("No duplicates found to delete.")

if __name__ == "__main__":
    main()
