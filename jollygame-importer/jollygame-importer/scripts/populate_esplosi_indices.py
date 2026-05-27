import sqlite3
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
DB_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\fluidra_clean.db'

# Query per aggiornare il metaobject
METAOBJECT_UPDATE = """
mutation metaobjectUpdate($id: ID!, $metaobject: MetaobjectUpdateInput!) {
  metaobjectUpdate(id: $id, metaobject: $metaobject) {
    userErrors { field message }
  }
}
"""

def get_shopify_active_products():
    # Recuperiamo i prodotti online (status: ACTIVE)
    query = """
    {
        products(first: 250, query: "status:active") {
            nodes {
                id
                variants(first: 1) { nodes { sku } }
            }
        }
    }
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query}, headers=headers)
    return response.json()['data']['products']['nodes']

def get_ricambio_metaobject_id(sku):
    # Query per trovare il Metaobject di tipo 'ricambio' con lo SKU corrispondente
    query = """
    query getMO($query: String!) {
        metaobjects(type: "ricambio", first: 1, query: $query) {
            nodes { id }
        }
    }
    """
    # Il campo è sku_originale
    query_str = f"sku_originale:{sku}"
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query, "variables": {"query": query_str}}, headers=headers)
    nodes = response.json()['data']['metaobjects']['nodes']
    return nodes[0]['id'] if nodes else None

def run():
    active_products = get_shopify_active_products()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Prodotti attivi trovati: {len(active_products)}")
    
    for sp in active_products:
        sku = sp['variants']['nodes'][0]['sku'] if sp['variants']['nodes'] else None
        if not sku: continue
        
        # Cerchiamo ricambi collegati a questo SKU padre
        cursor.execute("""
            SELECT pr.child_sku, pr.diagram_index 
            FROM product_relations pr
            WHERE pr.parent_sku = ?
        """, (sku,))
        
        ricambi_db = cursor.fetchall()
        
        for r_sku, r_index in ricambi_db:
            mo_id = get_ricambio_metaobject_id(r_sku)
            if mo_id:
                print(f"Aggiorno {r_sku} (Rif. {r_index}) -> {mo_id}")
                # Update Metaobject
                resp = requests.post(
                    f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json",
                    json={
                        "query": METAOBJECT_UPDATE,
                        "variables": {
                            "id": mo_id,
                            "metaobject": {
                                "fields": [{"key": "riferimento_esploso", "value": str(r_index)}]
                            }
                        }
                    },
                    headers={"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
                )
                if resp.json().get('data', {}).get('metaobjectUpdate', {}).get('userErrors', []):
                    print(f"  ❌ Errore: {resp.json()}")

if __name__ == "__main__":
    run()
