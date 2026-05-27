import sqlite3
import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
ROOT_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame'

DB_FILES = [
    os.path.join(ROOT_PATH, 'fluidra_clean.db'),
    os.path.join(ROOT_PATH, 'bestway_clean.db'),
    os.path.join(ROOT_PATH, 'intex_clean.db')
]

def shopify_request(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return {}

def create_doc_metaobject(title, url):
    mutation = """
    mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
      metaobjectCreate(metaobject: $metaobject) {
        metaobject { id }
        userErrors { field message }
      }
    }
    """
    variables = {
        "metaobject": {
            "type": "documento_tecnico",
            "fields": [
                {"key": "titolo", "value": title},
                {"key": "url_file", "value": url}
            ],
            "capabilities": { "publishable": { "status": "ACTIVE" } }
        }
    }
    res = shopify_request(mutation, variables)
    if res.get('errors'):
        print(f"  ❌ GraphQL Errors: {res['errors']}")
        return None
    if res.get('data', {}).get('metaobjectCreate', {}).get('userErrors'):
        print(f"  ❌ User Errors: {res['data']['metaobjectCreate']['userErrors']}")
        return None
    if res.get('data', {}).get('metaobjectCreate', {}).get('metaobject'):
        return res['data']['metaobjectCreate']['metaobject']['id']
    return None

def get_db_docs(sku, title):
    found_docs = []
    for db_path in DB_FILES:
        if not os.path.exists(db_path): continue
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            if sku:
                cursor.execute("SELECT docs_json FROM products WHERE sku = ?", (sku,))
                row = cursor.fetchone()
                if row and row[0] and row[0] != '[]':
                    found_docs = json.loads(row[0])
                    break
            clean_title = title.replace(' ', '%')
            cursor.execute("SELECT docs_json FROM products WHERE title LIKE ? AND docs_json != '[]'", (f"%{clean_title}%",))
            row = cursor.fetchone()
            if row and row[0]:
                found_docs = json.loads(row[0])
                break
        except: pass
    return found_docs

def run_sync():
    # 1. Get products
    query = """
    {
        products(first: 250, query: "status:active") {
            nodes {
                id
                title
                variants(first: 1) { nodes { sku } }
                metafield(namespace: "custom", key: "documentazione_tecnica") {
                    value
                }
            }
        }
    }
    """
    res = shopify_request(query)
    products = res['data']['products']['nodes']

    print(f"Analisi di {len(products)} prodotti per sincronizzazione manuali...")

    updated_count = 0
    for p in products:
        sku = p['variants']['nodes'][0]['sku'] if p['variants']['nodes'] else None
        shopify_docs = json.loads(p['metafield']['value']) if p['metafield'] else []
        
        # Se ha già documenti, saltiamo (per non duplicare o sovrascrivere se già OK)
        if shopify_docs: continue

        db_docs = get_db_docs(sku, p['title'])
        if not db_docs: continue

        print(f"📦 Caricamento {len(db_docs)} documenti per: {p['title']}...")
        new_mo_ids = []
        for doc in db_docs:
            name = doc.get('name') or doc.get('title') or "Manuale Tecnico"
            url = doc.get('url')
            if not url: continue
            
            mo_id = create_doc_metaobject(name, url)
            if mo_id:
                new_mo_ids.append(mo_id)
        
        if new_mo_ids:
            # Update product
            update_mutation = """
            mutation productUpdate($input: ProductInput!) {
              productUpdate(input: $input) {
                userErrors { field message }
              }
            }
            """
            shopify_request(update_mutation, {
                "input": {
                    "id": p['id'],
                    "metafields": [{
                        "namespace": "custom",
                        "key": "documentazione_tecnica",
                        "value": json.dumps(new_mo_ids)
                    }]
                }
            })
            print(f"  ✅ Collegati {len(new_mo_ids)} documenti.")
            updated_count += 1
            time.sleep(1) # Rate limit protection

    print(f"\n✨ Sincronizzazione completata! Prodotti aggiornati: {updated_count}")

if __name__ == "__main__":
    run_sync()
