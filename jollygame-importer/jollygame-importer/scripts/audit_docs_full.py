import sqlite3
import requests
import os
import json
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
                vendor
                metafield(namespace: "custom", key: "documentazione_tecnica") {
                    value
                }
                variants(first: 1) {
                    nodes {
                        sku
                    }
                }
            }
        }
    }
    """
    res = shopify_request(query)
    return res['data']['products']['nodes']

def check_db_for_docs(sku, title):
    found_docs = []
    for db_path in DB_FILES:
        if not os.path.exists(db_path): continue
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Column name might be docs_json in all
            # Try SKU first
            if sku:
                cursor.execute("SELECT docs_json FROM products WHERE sku = ?", (sku,))
                row = cursor.fetchone()
                if row and row[0] and row[0] != '[]':
                    found_docs = json.loads(row[0])
                    break
            
            # Try Title
            clean_title = title.replace(' ', '%')
            cursor.execute("SELECT docs_json FROM products WHERE title LIKE ? AND docs_json != '[]'", (f"%{clean_title}%",))
            row = cursor.fetchone()
            if row and row[0]:
                found_docs = json.loads(row[0])
                break
        except:
            pass
    return found_docs

def run_audit():
    shopify_products = get_shopify_active_products()
    
    report = {
        "ok": [],
        "missing_on_shopify_but_in_db": [],
        "missing_everywhere": []
    }
    
    for sp in shopify_products:
        sku = sp['variants']['nodes'][0]['sku'] if sp['variants']['nodes'] else None
        shopify_has_docs = sp['metafield'] is not None and sp['metafield']['value'] != "[]"
        
        if shopify_has_docs:
            report["ok"].append(sp['title'])
        else:
            db_docs = check_db_for_docs(sku, sp['title'])
            if db_docs:
                report["missing_on_shopify_but_in_db"].append({
                    "title": sp['title'],
                    "sku": sku,
                    "docs_count": len(db_docs),
                    "vendor": sp['vendor']
                })
            else:
                report["missing_everywhere"].append(f"{sp['title']} ({sp['vendor']})")
            
    print("\n--- 📊 AUDIT DOCUMENTAZIONE TECNICA TOTALE ---")
    print(f"✅ Prodotti con manuali su Shopify: {len(report['ok'])}")
    print(f"⚠️ Prodotti con manuali nei DB ma NON ancora caricati: {len(report['missing_on_shopify_but_in_db'])}")
    print(f"❌ Prodotti senza manuali né in Shopify né nei database locali: {len(report['missing_everywhere'])}")
    
    if report["missing_on_shopify_but_in_db"]:
        print("\n🔎 ESEMPI PRONTI PER IL CARICAMENTO (TOP 10):")
        for item in report["missing_on_shopify_but_in_db"][:10]:
            print(f"- [{item['vendor']}] {item['title']} -> {item['docs_count']} documenti")
            
    if report["missing_everywhere"]:
        print("\n📋 ALCUNI PRODOTTI CHE NECESSITANO DI CARICAMENTO MANUALE:")
        for item in report["missing_everywhere"][:10]:
            print(f"- {item}")

if __name__ == "__main__":
    run_audit()
