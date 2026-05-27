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
    print("🚀 Inizio Setup Metafield Esplosi...")

    # 1. Definizione Metafield per l'Immagine dell'Esploso (File Reference)
    mf_img_mutation = """
    mutation CreateMetafieldDef($definition: MetafieldDefinitionInput!) {
      metafieldDefinitionCreate(definition: $definition) {
        createdDefinition { id }
        userErrors { message }
      }
    }
    """
    
    mf_img_def = {
        "name": "Immagine Esploso",
        "namespace": "custom",
        "key": "immagine_esploso",
        "ownerType": "PRODUCT",
        "type": "file_reference",
        "description": "L'immagine del diagramma tecnico con i numeri."
    }
    
    res = shopify_request(mf_img_mutation, {"definition": mf_img_def})
    print("Metafield Immagine Result:", json.dumps(res, indent=2))

    # 2. Otteniamo l'ID della Metaobject Definition 'ricambio'
    mo_def_query = "{ metaobjectDefinitions(first: 50) { nodes { id type } } }"
    res_mo = shopify_request(mo_def_query)
    mo_id = next((n['id'] for n in res_mo['data']['metaobjectDefinitions']['nodes'] if n['type'] == 'ricambio'), None)

    if mo_id:
        # 3. Definizione Metafield per la lista di Ricambi (list.metaobject_reference)
        mf_list_def = {
            "name": "Lista Ricambi Esploso",
            "namespace": "custom",
            "key": "lista_ricambi_esploso",
            "ownerType": "PRODUCT",
            "type": "list.metaobject_reference",
            "validations": [{"name": "metaobject_definition_id", "value": mo_id}],
            "description": "Lista di ricambi collegati con il loro numero di riferimento."
        }
        
        res_list = shopify_request(mf_img_mutation, {"definition": mf_list_def})
        print("Metafield Lista Result:", json.dumps(res_list, indent=2))
    else:
        print("❌ Metaobject Definition 'ricambio' non trovata!")

if __name__ == "__main__":
    run()
