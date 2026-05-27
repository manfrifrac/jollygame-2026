import sqlite3
import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
DB_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\fluidra_clean.db'

def shopify_request(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return response.json()

def create_ricambio_mo(title, sku, index):
    mutation = """
    mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
      metaobjectCreate(metaobject: $metaobject) {
        metaobject { id }
      }
    }
    """
    res = shopify_request(mutation, {
        "metaobject": {
            "type": "ricambio",
            "fields": [
                {"key": "nome", "value": title},
                {"key": "sku_originale", "value": sku},
                {"key": "riferimento_esploso", "value": str(index)}
            ],
            "capabilities": { "publishable": { "status": "ACTIVE" } }
        }
    })
    return res.get('data', {}).get('metaobjectCreate', {}).get('metaobject', {}).get('id')

def run():
    # Robot target: CNX 50 iQ (handle: cnx-50-iq, id: gid://shopify/Product/15546245513564, SKU: WR000500)
    shopify_id = "gid://shopify/Product/15546245513564"
    parent_sku = "WR000500"
    
    print(f"📦 Forzatura Sincronizzazione per CNX 50 iQ...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT pr.child_sku, pr.diagram_index, p.title
        FROM product_relations pr
        JOIN products p ON pr.child_sku = p.sku
        WHERE pr.parent_sku = ?
    """, (parent_sku,))
    ricambi = cursor.fetchall()
    
    print(f"  ⚙️ Trovati {len(ricambi)} ricambi nel DB per SKU {parent_sku}.")
    
    mo_ids = []
    for r_sku, r_index, r_title in ricambi:
        full_name = f"{r_title} [CNX 50 iQ Rif.{r_index}]"
        mo_id = create_ricambio_mo(full_name, r_sku, r_index)
        if mo_id:
            mo_ids.append(mo_id)
            print(f"    ✅ Creato {r_sku} (Rif.{r_index})")

    if mo_ids:
        res = shopify_request("""
            mutation productUpdate($input: ProductInput!) {
              productUpdate(input: $input) { userErrors { message } }
            }
        """, {
            "input": {
                "id": shopify_id,
                "metafields": [
                    {
                        "namespace": "custom",
                        "key": "lista_ricambi_esploso",
                        "value": json.dumps(mo_ids)
                    }
                ]
            }
        })
        print(f"  🔗 Sincronizzazione completata per CNX 50 iQ: {res}")

if __name__ == "__main__":
    run()
