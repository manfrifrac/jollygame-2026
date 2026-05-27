import sqlite3
import requests
import os
import json
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

def get_shopify_docs():
    query = """
    {
        products(first: 250, query: "status:active") {
            nodes {
                id
                title
                handle
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

def run_audit():
    shopify_products = get_shopify_docs()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    report = {
        "ok": [],
        "missing_on_shopify_but_in_db": [],
        "missing_everywhere": []
    }
    
    for sp in shopify_products:
        sku = sp['variants']['nodes'][0]['sku'] if sp['variants']['nodes'] else None
        shopify_has_docs = sp['metafield'] is not None and sp['metafield']['value'] != "[]"
        
        # Check DB
        db_docs = []
        if sku:
            cursor.execute("SELECT docs_json FROM products WHERE sku = ?", (sku,))
            row = cursor.fetchone()
            if row and row[0]:
                db_docs = json.loads(row[0])
        
        if not db_docs:
            clean_title = sp['title'].replace(' ', '%')
            cursor.execute("SELECT docs_json FROM products WHERE title LIKE ? AND docs_json != '[]'", (f"%{clean_title}%",))
            row = cursor.fetchone()
            if row and row[0]:
                db_docs = json.loads(row[0])
        
        if shopify_has_docs:
            report["ok"].append(sp['title'])
        elif db_docs:
            report["missing_on_shopify_but_in_db"].append({
                "title": sp['title'],
                "sku": sku,
                "docs_count": len(db_docs)
            })
        else:
            report["missing_everywhere"].append(sp['title'])
            
    print("\n--- 📊 AUDIT DOCUMENTAZIONE TECNICA ---")
    print(f"✅ Prodotti con manuali su Shopify: {len(report['ok'])}")
    print(f"⚠️ Prodotti con manuali nel DB ma NON su Shopify: {len(report['missing_on_shopify_but_in_db'])}")
    print(f"❌ Prodotti senza manuali né in Shopify né nel DB: {len(report['missing_everywhere'])}")
    
    if report["missing_on_shopify_but_in_db"]:
        print("\n🔎 ESEMPI DA CARICARE DAL DB:")
        for item in report["missing_on_shopify_but_in_db"][:10]:
            print(f"- {item['title']} (SKU: {item['sku']}) -> {item['docs_count']} documenti pronti nel DB")

if __name__ == "__main__":
    run_audit()
