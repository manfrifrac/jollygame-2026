import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

def run():
    query = """
    {
        productByHandle(handle: "cnx-50-iq") {
            id
            title
            metafields(first: 20, namespace: "custom") {
                nodes {
                    key
                    value
                    type
                }
            }
        }
    }
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query}, headers=headers)
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    run()
