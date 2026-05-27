import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

def check_product(handle):
    query = """
    query getProduct($handle: String!) {
        productByHandle(handle: $handle) {
            id
            title
            metafields(first: 10, namespace: "custom") {
                nodes {
                    key
                    value
                }
            }
        }
    }
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query, "variables": {"handle": handle}}, headers=headers)
    return response.json()

def run():
    for h in ["ms", "freedom-lite"]:
        res = check_product(h)
        print(f"--- {h} ---")
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    run()
