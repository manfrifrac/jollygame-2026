import requests
import os
import json
import sqlite3
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
ROOT_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame'

def shopify_request(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        res_json = response.json()
        if 'errors' in res_json:
            print(f"❌ Shopify API Errors: {json.dumps(res_json['errors'], indent=2)}")
        return res_json
    except Exception as e:
        print(f"❌ Network/JSON Error: {e}")
        return {}

def run_deep_audit():
    # 1. Recuperiamo i prodotti Shopify che non hanno né esploso né documenti
    query = """
    {
        products(first: 250, query: "status:active") {
            nodes {
                id
                title
                handle
                vendor
                metafield_docs: metafield(namespace: "custom", key: "documentazione_tecnica") { value }
                metafield_esploso: metafield(namespace: "custom", key: "immagine_esploso") { value }
                variants(first: 1) { nodes { sku barcode } }
            }
        }
    }
    """
    res = shopify_request(query)
    if 'data' not in res or not res['data']:
        print("❌ Impossibile recuperare i prodotti da Shopify. Verificare i log sopra.")
        return

    products = res['data']['products']['nodes']
    
    missing_products = []
    for p in products:
        has_docs = p['metafield_docs'] and p['metafield_docs']['value'] != "[]"
        has_esploso = p['metafield_esploso'] and p['metafield_esploso']['value'] != ""
        if not has_docs and not has_esploso:
            sku = p['variants']['nodes'][0]['sku'] if p['variants']['nodes'] else None
            ean = p['variants']['nodes'][0]['barcode'] if p['variants']['nodes'] else None
            missing_products.append({"title": p['title'], "sku": sku, "ean": ean, "vendor": p['vendor']})

    print(f"Audit su {len(missing_products)} prodotti potenzialmente mancanti...\n")

    db_paths = {
        "Fluidra": os.path.join(ROOT_PATH, 'fluidra_clean.db'),
        "Bestway": os.path.join(ROOT_PATH, 'bestway_clean.db'),
        "Intex": os.path.join(ROOT_PATH, 'intex_clean.db')
    }

    results = []

    for p in missing_products:
        found_in = []
        possible_docs = []
        possible_relations = 0
        
        for name, path in db_paths.items():
            if not os.path.exists(path): continue
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            # Tabella prodotti varia per nome in Bestway
            table = "products" if name != "Bestway" else "bestway_products"
            col_docs = "docs_json" if name == "Fluidra" else ("pdfs" if name == "Intex" else "images") # Bestway non ha pdfs?
            
            # Ricerca FUZZY per titolo (molto permissiva)
            search_title = p['title'].replace('Piscina', '').replace('Robot', '').strip()
            # Prendiamo le prime 2 parole significative
            words = search_title.split()[:2]
            fuzzy_query = "%" + "%".join(words) + "%"
            
            query_db = f"SELECT sku, title, {col_docs if col_docs in ['docs_json','pdfs'] else 'sku'} FROM {table} WHERE (sku = ? OR title LIKE ? OR ean = ?) AND is_spare_part = 0 LIMIT 1"
            cursor.execute(query_db, (p['sku'], fuzzy_query, p['ean']))
            match = cursor.fetchone()
            
            if match:
                found_in.append(name)
                # Controlliamo relazioni
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_relations'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM product_relations WHERE parent_sku = ?", (match[0],))
                    possible_relations = cursor.fetchone()[0]
                else:
                    possible_relations = 0
                
            conn.close()
        
        if found_in:
            results.append({
                "product": p['title'],
                "vendor": p['vendor'],
                "found_in_db": found_in,
                "potential_relations": possible_relations
            })

    print(f"--- 🕵️ RISULTATI RICERCA PROFONDA ---")
    if not results:
        print("Nessun match nascosto trovato con la ricerca fuzzy.")
    else:
        for r in results:
            print(f"🔍 '{r['product']}' ({r['vendor']})")
            print(f"   Trovato in: {', '.join(r['found_in_db'])}")
            print(f"   Relazioni ricambi trovate: {r['potential_relations']}")
            print("-" * 30)

if __name__ == "__main__":
    run_deep_audit()
