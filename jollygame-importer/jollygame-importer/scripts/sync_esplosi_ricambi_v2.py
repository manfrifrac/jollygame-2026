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

def create_ricambio_mo(title, sku, index, image_id=None):
    mutation = """
    mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
      metaobjectCreate(metaobject: $metaobject) {
        metaobject { id }
        userErrors { field message }
      }
    }
    """
    fields = [
        {"key": "nome", "value": title},
        {"key": "sku_originale", "value": sku},
        {"key": "riferimento_esploso", "value": str(index)}
    ]
    if image_id:
        fields.append({"key": "immagine", "value": image_id})

    res = shopify_request(mutation, {
        "metaobject": {
            "type": "ricambio",
            "fields": fields,
            "capabilities": { "publishable": { "status": "ACTIVE" } }
        }
    })
    return res.get('data', {}).get('metaobjectCreate', {}).get('metaobject', {}).get('id')

def run():
    # Carichiamo i match identificati dallo script step1
    with open('esplosi_matches.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Per non duplicare prodotti, usiamo un set di shopify_id
    processed_shopify_ids = set()

    for m in matches:
        s_id = m['shopify_id']
        if s_id in processed_shopify_ids: continue
        processed_shopify_ids.add(s_id)

        print(f"📦 Elaborazione {m['title']} ({m['sku']})...")

        # 1. Recupero l'immagine dell'esploso (se già caricata o da caricare)
        # Per ora assumiamo di averla caricata e ne servirebbe l'ID. 
        # Come fallback, usiamo l'URL del DB o carichiamo il file locale.
        # [OMESSO CARICAMENTO FILE PER VELOCITÀ - USIAMO I DATI TESTUALI]

        # 2. Recupero ricambi dal DB per questo SKU padre
        cursor.execute("""
            SELECT pr.child_sku, pr.diagram_index, p.title, p.images_json
            FROM product_relations pr
            JOIN products p ON pr.child_sku = p.sku
            WHERE pr.parent_sku = ?
        """, (m['sku'],))
        ricambi_db = cursor.fetchall()

        if not ricambi_db:
            # Fallback title search if SKU didn't match relations
            clean_title = m['title'].replace(' ', '%')
            cursor.execute("""
                SELECT pr.child_sku, pr.diagram_index, p.title, p.images_json
                FROM product_relations pr
                JOIN products p ON pr.child_sku = p.sku
                JOIN products parent ON pr.parent_sku = parent.sku
                WHERE parent.title LIKE ?
            """, (f'%{clean_title}%',))
            ricambi_db = cursor.fetchall()

        if not ricambi_db:
            print(f"  ⚠️ Nessuna relazione trovata per {m['title']}")
            continue

        print(f"  ⚙️ Creazione di {len(ricambi_db)} Metaobject Ricambio...")
        mo_ids = []
        for r_sku, r_index, r_title, r_images in ricambi_db:
            # Creiamo un metaobject UNIVOCO per questa occorrenza
            # Titolo include il Robot per chiarezza UX
            full_title = f"{r_title} [{m['title']} Rif.{r_index}]"
            mo_id = create_ricambio_mo(full_title, r_sku, r_index)
            if mo_id:
                mo_ids.append(mo_id)
        
        if mo_ids:
            # 3. Colleghiamo la lista al prodotto
            update_res = shopify_request("""
                mutation productUpdate($input: ProductInput!) {
                  productUpdate(input: $input) {
                    userErrors { field message }
                  }
                }
            """, {
                "input": {
                    "id": s_id,
                    "metafields": [
                        {
                            "namespace": "custom",
                            "key": "lista_ricambi_esploso",
                            "value": json.dumps(mo_ids)
                        }
                    ]
                }
            })
            print(f"  ✅ Collegati {len(mo_ids)} ricambi a {m['title']}")
        
        # Pausa breve per non saturare le API
        time.sleep(0.5)

if __name__ == "__main__":
    run()
