import sqlite3
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
DB_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\fluidra_clean.db'

METAOBJECT_UPDATE = """
mutation metaobjectUpdate($id: ID!, $metaobject: MetaobjectUpdateInput!) {
  metaobjectUpdate(id: $id, metaobject: $metaobject) {
    userErrors { field message }
  }
}
"""

def get_ricambio_mo_by_sku(sku):
    query = """
    query getMO($query: String!) {
        metaobjects(type: "ricambio", first: 1, query: $query) {
            nodes { id }
        }
    }
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query, "variables": {"query": f"sku_originale:{sku}"}}, headers=headers)
    data = response.json()
    if data['data']['metaobjects']['nodes']:
        return data['data']['metaobjects']['nodes'][0]['id']
    return None

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Recuperiamo le relazioni padre-figlio dal database
    cursor.execute("SELECT parent_sku, child_sku, diagram_index FROM product_relations")
    relazioni = cursor.fetchall()
    
    print(f"Relazioni trovate nel DB: {len(relazioni)}")
    
    # 2. Aggiorniamo i Metaobject "Ricambio" con l'indice corretto
    count = 0
    for p_sku, c_sku, d_index in relazioni:
        mo_id = get_ricambio_mo_by_sku(c_sku)
        if mo_id and d_index:
            # Aggiorniamo il riferimento esploso (numero) nel metaobject del ricambio
            resp = requests.post(
                f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json",
                json={
                    "query": METAOBJECT_UPDATE,
                    "variables": {
                        "id": mo_id,
                        "metaobject": {
                            "fields": [{"key": "riferimento_esploso", "value": str(d_index)}]
                        }
                    }
                },
                headers={"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
            )
            
            data = resp.json()
            if not data.get('data', {}).get('metaobjectUpdate', {}).get('userErrors'):
                count += 1
            else:
                print(f"  ❌ Errore aggiornamento {c_sku}: {data}")

    print(f"Aggiornamento completato: {count} riferimenti esplosi impostati.")

if __name__ == "__main__":
    run()
