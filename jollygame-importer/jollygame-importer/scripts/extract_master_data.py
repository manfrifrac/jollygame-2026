import sqlite3
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv('SHOP_DOMAIN')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
ROOT_PATH = r'C:\Users\Riccardo\Desktop\Manfredo\JollyGame'

DB_PATHS = {
    "Fluidra": os.path.join(ROOT_PATH, 'fluidra_clean.db'),
    "Bestway": os.path.join(ROOT_PATH, 'bestway_clean.db'),
    "Intex": os.path.join(ROOT_PATH, 'intex_clean.db')
}

def shopify_request(query, variables=None):
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    return response.json()

def get_shopify_products():
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
    return res['data']['products']['nodes']

def get_db_match(sku, title, barcode):
    for name, path in DB_PATHS.items():
        if not os.path.exists(path): continue
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        table = "products" if name != "Bestway" else "bestway_products"
        
        # Check if diagram_url column exists
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [c[1] for c in cursor.fetchall()]
        has_diag = 'diagram_url' in cols
        diag_col = "diagram_url" if has_diag else "NULL"

        # Try exact SKU
        cursor.execute(f"SELECT sku, title, {diag_col} FROM {table} WHERE sku = ? AND is_spare_part = 0 LIMIT 1", (sku,))
        match = cursor.fetchone()
        
        if not match:
            # Try fuzzy title
            clean_title = title.replace('Piscina', '').replace('Robot', '').strip()
            words = clean_title.split()[:2]
            fuzzy_query = "%" + "%".join(words) + "%"
            cursor.execute(f"SELECT sku, title, {diag_col} FROM {table} WHERE title LIKE ? AND is_spare_part = 0 LIMIT 1", (fuzzy_query,))
            match = cursor.fetchone()
            
        if match:
            # Get relations and spare part data (including images)
            rel_sku = match[0]
            diag_url = match[2]
            
            # Check if product_relations table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_relations'")
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info(product_relations)")
                rel_cols = [c[1] for c in cursor.fetchall()]
                
                idx_col = "diagram_index" if "diagram_index" in rel_cols else ("relation_type" if "relation_type" in rel_cols else "NULL")
                
                cursor.execute(f"""
                    SELECT pr.child_sku, pr.{idx_col}, p.title, 
                           { "p.images_json" if name == "Fluidra" else "p.images" }
                    FROM product_relations pr
                    JOIN {table} p ON pr.child_sku = p.sku
                    WHERE pr.parent_sku = ?
                """, (rel_sku,))
                ricambi = cursor.fetchall()
            else:
                ricambi = []
                
            conn.close()
            return {
                "db": name,
                "sku": rel_sku,
                "diagram_url": diag_url,
                "ricambi": [
                    {"sku": r[0], "index": r[1], "title": r[2], "images": r[3]} for r in ricambi
                ]
            }
        conn.close()
    return None

def run():
    products = get_shopify_products()
    print(f"Analisi di {len(products)} prodotti Shopify...")
    
    master_data = []
    for p in products:
        sku = p['variants']['nodes'][0]['sku'] if p['variants']['nodes'] else None
        barcode = p['variants']['nodes'][0]['barcode'] if p['variants']['nodes'] else None
        
        match = get_db_match(sku, p['title'], barcode)
        if match:
            print(f"✅ Match trovato per {p['title']} in {match['db']} ({len(match['ricambi'])} ricambi)")
            master_data.append({
                "shopify_id": p['id'],
                "shopify_title": p['title'],
                "db": match['db'],
                "db_sku": match['sku'],
                "diagram_url": match['diagram_url'],
                "ricambi": match['ricambi'],
                "current_docs": p['metafield_docs']['value'] if p['metafield_docs'] else "[]"
            })
            
    with open('master_sync_data.json', 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=2)
    print(f"\nGenerato master_sync_data.json con {len(master_data)} prodotti pronti.")

if __name__ == "__main__":
    run()
