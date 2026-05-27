import sqlite3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

def get_shopify_products():
    # Ottiene i prodotti per confrontare i titoli/SKU
    # Nota: GraphQL query ottimizzata
    query = """
    {
        products(first: 250) {
            nodes {
                id
                title
                handle
                variants(first: 1) {
                    nodes {
                        sku
                    }
                }
            }
        }
    }
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query}, headers=headers)
    return response.json()['data']['products']['nodes']

def run():
    shopify_products = get_shopify_products()
    conn = sqlite3.connect(r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\fluidra_clean.db')
    cursor = conn.cursor()
    
    print(f"Ho analizzato {len(shopify_products)} prodotti Shopify.")
    print("Confronto in corso con database Fluidra (diagram_url)...")
    print("-" * 50)
    
    found_count = 0
    for sp in shopify_products:
        sku = sp['variants']['nodes'][0]['sku'] if sp['variants']['nodes'] else None
        
        # Cerchiamo per SKU (spesso vuoto o diverso) o per Title (pulito)
        # Proviamo prima lo SKU
        if sku:
            cursor.execute("SELECT title, diagram_url FROM products WHERE sku = ? AND diagram_url IS NOT NULL AND diagram_url != ''", (sku,))
            db_product = cursor.fetchone()
        else:
            db_product = None
            
        # Fallback: se SKU non trovato, cerchiamo per titolo pulito
        if not db_product:
            clean_title = sp['title'].replace(' ', '%')
            cursor.execute("SELECT title, diagram_url FROM products WHERE title LIKE ? AND diagram_url IS NOT NULL AND diagram_url != '' LIMIT 1", (f'%{clean_title}%',))
            db_product = cursor.fetchone()
        
        if db_product:
            print(f"✅ TROVATO: {sp['title']} -> {db_product[1]}")
            found_count += 1
            
    print("-" * 50)
    print(f"Totale corrispondenze trovate: {found_count}")

if __name__ == "__main__":
    run()
