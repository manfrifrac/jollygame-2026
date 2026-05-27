import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

def shopify_request(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return response.json()

def run():
    mutation = """
    mutation metaobjectDefinitionUpdate($id: ID!, $definition: MetaobjectDefinitionUpdateInput!) {
      metaobjectDefinitionUpdate(id: $id, definition: $definition) {
        metaobjectDefinition { id }
        userErrors { field message }
      }
    }
    """
    
    # ID di Documento Tecnico
    def_id = "gid://shopify/MetaobjectDefinition/35641753948"
    
    variables = {
        "id": def_id,
        "definition": {
            "capabilities": {
                "publishable": { "enabled": True }
            }
        }
    }
    
    res = shopify_request(mutation, variables)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    run()
