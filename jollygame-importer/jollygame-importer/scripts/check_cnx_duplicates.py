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
        products(first: 50, query: "title:'CNX 50 iQ'") {
            nodes {
                id
                handle
                title
                metafields(first: 20, namespace: "custom") {
                    nodes {
                        key
                        value
                    }
                }
            }
        }
    }
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query}, headers=headers)
    print(json.dumps(response.json()['data']['products']['nodes'], indent=2))

if __name__ == "__main__":
    run()
