import json
import requests
import os
from dotenv import dotenv_values

# Load Shopify credentials
env_path = 'jollygame-importer/jollygame-importer/.env'
env_config = dotenv_values(env_path)
SHOP_DOMAIN = env_config.get('SHOP_DOMAIN')
ACCESS_TOKEN = env_config.get('SHOPIFY_ACCESS_TOKEN')

def get_gre_status_summary():
    url = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN}
    
    products_summary = {
        "ACTIVE": [],
        "DRAFT": [],
        "ARCHIVED": []
    }
    
    cursor = None
    has_next_page = True
    
    print("Recupero stato prodotti Gre da Shopify...")
    
    while has_next_page:
        query = """
        query($cursor: String) {
          products(first: 250, query: "vendor:Gre", after: $cursor) {
            pageInfo { hasNextPage endCursor }
            edges {
              node {
                id
                title
                status
                publishedAt
                variantsCount { count }
              }
            }
          }
        }
        """
        response = requests.post(url, json={"query": query, "variables": {"cursor": cursor}}, headers=headers)
        data = response.json()
        
        if "errors" in data:
            print("Errore:", data["errors"])
            break
            
        edges = data["data"]["products"]["edges"]
        for edge in edges:
            node = edge["node"]
            status = node["status"]
            products_summary[status].append({
                "title": node["title"],
                "published": node["publishedAt"] is not None,
                "variants": node["variantsCount"]["count"]
            })
            
        has_next_page = data["data"]["products"]["pageInfo"]["hasNextPage"]
        cursor = data["data"]["products"]["pageInfo"]["endCursor"]
        
    return products_summary

if __name__ == "__main__":
    summary = get_gre_status_summary()
    
    print("\n📊 RIEPILOGO STATO PRODOTTI GRE:")
    print(f"✅ ATTIVI (Online): {len(summary['ACTIVE'])}")
    for p in summary['ACTIVE'][:10]:
        print(f"   - {p['title']} ({p['variants']} varianti)")
    if len(summary['ACTIVE']) > 10: print("   ... e altri")

    print(f"\n📝 BOZZE (Draft): {len(summary['DRAFT'])}")
    for p in summary['DRAFT'][:10]:
        print(f"   - {p['title']} ({p['variants']} varianti)")
    if len(summary['DRAFT']) > 10: print("   ... e altri")

    print(f"\n📦 ARCHIVIATI: {len(summary['ARCHIVED'])}")
    
    total_variants = sum(p['variants'] for s in summary.values() for p in s)
    print(f"\n🔹 Totale Varianti (SKU) mappati: {total_variants}")
