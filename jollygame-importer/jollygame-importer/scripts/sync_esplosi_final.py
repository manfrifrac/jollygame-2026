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

def get_shopify_active_products():
    query = """
    {
        products(first: 250, query: "status:active") {
            nodes {
                id
                title
                handle
                variants(first: 1) { nodes { sku } }
            }
        }
    }
    """
    res = shopify_request(query)
    return res['data']['products']['nodes']

def upload_file_from_url(url, filename):
    # Nota: Caricare file via URL su Shopify richiede stagedUploads.
    # Per semplicità in questo script, se il diagramma è già una URL valida Fluidra,
    # Shopify Files API può accettarla o possiamo caricarla come GenericFile.
    # Ma dato che abbiamo già le immagini caricate (step precedenti),
    # cercheremo di recuperare l'ID del file se già caricato o procediamo al caricamento rapido.
    pass

def create_ricambio_mo(data):
    mutation = """
    mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
      metaobjectCreate(metaobject: $metaobject) {
        metaobject { id }
        userErrors { field message }
      }
    }
    """
    res = shopify_request(mutation, {"metaobject": data})
    return res['data']['metaobjectCreate']['metaobject']['id'] if res.get('data', {}).get('metaobjectCreate', {}).get('metaobject') else None

def run():
    active_products = get_shopify_active_products()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Sincronizzazione di {len(active_products)} prodotti attivi...")

    for sp in active_products:
        sku = sp['variants']['nodes'][0]['sku'] if sp['variants']['nodes'] else None
        if not sku: continue

        # 1. Recupera Diagram URL e Ricambi dal DB
        cursor.execute("SELECT diagram_url FROM products WHERE sku = ?", (sku,))
        diag_row = cursor.fetchone()
        diagram_url = diag_row[0] if diag_row else None

        cursor.execute("""
            SELECT pr.child_sku, pr.diagram_index, p.title, p.images_json
            FROM product_relations pr
            JOIN products p ON pr.child_sku = p.sku
            WHERE pr.parent_sku = ?
        """, (sku,))
        ricambi_db = cursor.fetchall()

        if not ricambi_db: continue

        print(f"📦 Prodotto: {sp['title']} ({sku}) - {len(ricambi_db)} ricambi.")

        # 2. Crea i Metaobject Ricambio specifici per questo prodotto
        mo_ids = []
        for r_sku, r_index, r_title, r_images in ricambi_db:
            # Estraiamo l'immagine del ricambio se presente
            img_list = json.loads(r_images) if r_images else []
            img_url = img_list[0] if img_list else None
            
            # Qui dovremmo caricare l'immagine se non è già su Shopify, 
            # ma per velocità ora popoliamo i dati testuali e il riferimento.
            
            mo_data = {
                "type": "ricambio",
                "fields": [
                    {"key": "nome", "value": f"{r_title}"},
                    {"key": "sku_originale", "value": r_sku},
                    {"key": "riferimento_esploso", "value": str(r_index)}
                ],
                "capabilities": { "publishable": { "status": "ACTIVE" } }
            }
            
            # TODO: Caricamento immagine ricambio se img_url presente
            
            mo_id = create_ricambio_mo(mo_data)
            if mo_id:
                mo_ids.append(mo_id)
        
        # 3. Collega la lista di Metaobject al prodotto Shopify
        if mo_ids:
            update_mutation = """
            mutation productUpdate($input: ProductInput!) {
              productUpdate(input: $input) {
                userErrors { field message }
              }
            }
            """
            shopify_request(update_mutation, {
                "input": {
                    "id": sp['id'],
                    "metafields": [
                        {
                            "namespace": "custom",
                            "key": "lista_ricambi_esploso",
                            "value": json.dumps(mo_ids)
                        }
                    ]
                }
            })
            print(f"  ✅ Collegati {len(mo_ids)} ricambi.")

if __name__ == "__main__":
    run()
