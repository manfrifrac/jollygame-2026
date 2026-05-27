import sqlite3
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
DB_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\fluidra_clean.db'
DOWNLOAD_DIR = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame\downloads\esplosi'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_shopify_products():
    query = """
    {
        products(first: 250) {
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
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query}, headers=headers)
    return response.json()['data']['products']['nodes']

def download_image(url, sku):
    try:
        ext = url.split('.')[-1].split('?')[0].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            ext = 'jpg'
        filename = f"{sku}_esploso.{ext}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        if os.path.exists(filepath):
            return filepath

        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return filepath
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def run():
    shopify_products = get_shopify_products()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    matches = []
    for sp in shopify_products:
        sku = sp['variants']['nodes'][0]['sku'] if sp['variants']['nodes'] else None
        if not sku:
            # Fallback to title
            clean_title = sp['title'].replace(' ', '%')
            cursor.execute("SELECT sku, diagram_url FROM products WHERE title LIKE ? AND diagram_url IS NOT NULL AND diagram_url != '' LIMIT 1", (f'%{clean_title}%',))
        else:
            cursor.execute("SELECT sku, diagram_url FROM products WHERE sku = ? AND diagram_url IS NOT NULL AND diagram_url != ''", (sku,))
        
        db_product = cursor.fetchone()
        if db_product:
            matches.append({
                'shopify_id': sp['id'],
                'title': sp['title'],
                'sku': sku or db_product[0],
                'diagram_url': db_product[1],
                'current_docs': sp['metafield']['value'] if sp['metafield'] else "[]"
            })

    print(f"Inizio download di {len(matches)} esplosi...")
    
    for match in matches:
        print(f"Processing: {match['title']} ({match['sku']})")
        local_file = download_image(match['diagram_url'], match['sku'])
        if local_file:
            match['local_file'] = local_file
            print(f"  ✅ Downloaded: {local_file}")
        else:
            print(f"  ❌ Failed download: {match['diagram_url']}")

    # Save matches to a temp file for the next stage
    import json
    with open('esplosi_matches.json', 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2)

if __name__ == "__main__":
    run()
