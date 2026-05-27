import requests
import os
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

def shopify_request(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return response.json()

def get_all_metaobjects_by_type(type_name):
    query = """
    query getMOs($type: String!) {
        metaobjects(type: $type, first: 250) {
            nodes { id handle }
        }
    }
    """
    res = shopify_request(query, {"type": type_name})
    return res['data']['metaobjects']['nodes']

def run():
    # 1. Cancelliamo i Metaobject di relazione "Associazione Ricambio" se ne avessimo creati
    # (Non ne abbiamo ancora creati molti, ma puliamo i Documento Tecnico che potremmo aver creato errati)
    docs = get_all_metaobjects_by_type("documento_tecnico")
    print(f"Pulizia di {len(docs)} documenti tecnici...")
    for doc in docs:
        print(f"Eliminazione {doc['id']}...")
        shopify_request("mutation delete($id: ID!) { metaobjectDelete(id: $id) { userErrors { message } } }", {"id": doc['id']})

    # 2. Pulizia Metafield sui prodotti (rimuoviamo il collegamento custom.documentazione_tecnica)
    # Questa operazione è delicata, la facciamo solo se necessario o sovrascriviamo semplicemente.
    print("Pulizia completata.")

if __name__ == "__main__":
    run()
