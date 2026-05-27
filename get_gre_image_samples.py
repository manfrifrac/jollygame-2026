import requests
import os
from dotenv import dotenv_values

env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)
SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def get_sample_images():
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    query = """
    query {
      products(first: 20, query: "vendor:Gre") {
        edges {
          node {
            title
            images(first: 5) {
              edges {
                node {
                  url
                }
              }
            }
          }
        }
      }
    }
    """
    response = requests.post(url, json={"query": query}, headers=headers)
    data = response.json()
    if 'errors' in data:
        print(data['errors'])
        return

    for edge in data['data']['products']['edges']:
        node = edge['node']
        imgs = [img['node']['url'] for img in node['images']['edges']]
        if imgs:
            print(f"Product: {node['title']}")
            for img in imgs:
                print(f"  - {img}")

if __name__ == "__main__":
    get_sample_images()
