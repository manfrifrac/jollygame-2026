
import dotenv
import os
import requests

dotenv.load_dotenv('jollygame-importer/jollygame-importer/.env')

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_URL = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"

def run_query(query, variables=None):
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=headers)
    return response.json()

if __name__ == "__main__":
    sku = "KPEOV5027"
    query = f'''
    {{
      products(first: 1, query: "sku:{sku}") {{
        nodes {{
          id
          title
          handle
          metafields(first: 20) {{
            nodes {{
              namespace
              key
              value
            }}
          }}
        }}
      }}
    }}
    '''
    res = run_query(query)
    print(res)
