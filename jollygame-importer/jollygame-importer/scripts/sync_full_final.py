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
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=30)
        return response.json()
    except Exception as e:
        print(f"  ⚠️ Error request: {e}")
        return {}

def upload_file_shopify(file_path):
    staged_mutation = """
    mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
      stagedUploadsCreate(input: $input) {
        stagedTargets { url resourceUrl parameters { name value } }
      }
    }
    """
    file_name = os.path.basename(file_path)
    file_size = str(os.path.getsize(file_path))
    
    res = shopify_request(staged_mutation, {
        "input": [{ "filename": file_name, "mimeType": "image/jpeg", "resource": "IMAGE", "fileSize": file_size, "httpMethod": "POST" }]
    })
    
    if not res.get('data', {}).get('stagedUploadsCreate', {}).get('stagedTargets'):
        return None
    
    target = res['data']['stagedUploadsCreate']['stagedTargets'][0]
    payload = {p['name']: p['value'] for p in target['parameters']}
    
    with open(file_path, 'rb') as f:
        r = requests.post(target['url'], data=payload, files={'file': f})
    
    if r.status_code not in [200, 201]:
        return None

    file_create_mutation = """
    mutation fileCreate($files: [FileCreateInput!]!) {
      fileCreate(files: $files) { files { id } }
    }
    """
    res_file = shopify_request(file_create_mutation, {
        "files": [{ "alt": "Esploso", "contentType": "IMAGE", "originalSource": target['resourceUrl'] }]
    })
    
    files = res_file.get('data', {}).get('fileCreate', {}).get('files')
    return files[0]['id'] if files else None

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
    with open('esplosi_matches.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    processed_ids = set()

    for m in matches:
        if m['shopify_id'] in processed_ids: continue
        processed_ids.add(m['shopify_id'])

        print(f"📦 Robot: {m['title']}...")
        
        # 1. Esploso
        if 'local_file' in m and os.path.exists(m['local_file']):
            diag_id = upload_file_shopify(m['local_file'])
            if diag_id:
                shopify_request("""
                    mutation productUpdate($input: ProductInput!) {
                      productUpdate(input: $input) { userErrors { message } }
                    }
                """, {
                    "input": {
                        "id": m['shopify_id'],
                        "metafields": [{ "namespace": "custom", "key": "immagine_esploso", "value": diag_id }]
                    }
                })
                print(f"  🖼️ Esploso caricato.")

        # 2. Ricambi
        cursor.execute("SELECT pr.child_sku, pr.diagram_index, p.title FROM product_relations pr JOIN products p ON pr.child_sku = p.sku WHERE pr.parent_sku = ?", (m['sku'],))
        ricambi = cursor.fetchall()
        
        mo_ids = []
        for r_sku, r_index, r_title in ricambi:
            full_name = f"{r_title} [{m['title']} Rif.{r_index}]"
            mo_id = create_ricambio_mo(full_name, r_sku, r_index)
            if mo_id: mo_ids.append(mo_id)
        
        if mo_ids:
            shopify_request("""
                mutation productUpdate($input: ProductInput!) {
                  productUpdate(input: $input) { userErrors { message } }
                }
            """, {
                "input": {
                    "id": m['shopify_id'],
                    "metafields": [{ "namespace": "custom", "key": "lista_ricambi_esploso", "value": json.dumps(mo_ids) }]
                }
            })
            print(f"  🔗 {len(mo_ids)} ricambi collegati.")
        
        time.sleep(2) # Rallentiamo per evitare limiti Shopify

if __name__ == "__main__":
    run()
