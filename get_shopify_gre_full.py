import pandas as pd
import json
import requests
import os
from dotenv import dotenv_values

env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)
SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

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
                productType
                options { name values }
                variants(first: 50) {
                  edges {
                    node {
                      id
                      sku
                      title
                      selectedOptions { name value }
                      image { url }
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
        if "errors" in data: 
            print(data["errors"])
            break
        edges = data["data"]["products"]["edges"]
        for edge in edges:
            node = edge["node"]
            variants = []
            for v in node["variants"]["edges"]:
                vn = v['node']
                variants.append({
                    "id": vn["id"],
                    "sku": vn["sku"],
                    "title": vn["title"],
                    "options": {opt["name"]: opt["value"] for opt in vn["selectedOptions"]},
                    "image": vn["image"]["url"] if vn["image"] else None
                })
            products.append({
                "id": node["id"],
                "title": node["title"],
                "status": node["status"],
                "type": node["productType"],
                "options": [opt["name"] for opt in node["options"]],
                "variants": variants
            })
        has_next_page = data["data"]["products"]["pageInfo"]["hasNextPage"]
        cursor = data["data"]["products"]["pageInfo"]["endCursor"]
    return products

if __name__ == "__main__":
    shopify_gre = get_all_gre_shopify()
    with open('shopify_gre_full_data.json', 'w') as f:
        json.dump(shopify_gre, f, indent=4)
    print(f"Retrieved {len(shopify_gre)} Gre products from Shopify.")
