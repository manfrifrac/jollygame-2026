import asyncio
import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="jollygame-importer/jollygame-importer/.env")

SHOP_DOMAIN = os.getenv("SHOP_DOMAIN", "jollygamepiscine.myshopify.com")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
GRAPHQL_URL = f"https://{SHOP_DOMAIN}/admin/api/2024-10/graphql.json"

async def shopify_request(query, variables=None):
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN,
    }
    payload = {"query": query, "variables": variables}
    async with httpx.AsyncClient() as client:
        res = await client.post(GRAPHQL_URL, json=payload, headers=headers, timeout=30.0)
        return res.json()

# Dati consolidati (SKU -> Prezzo)
FINAL_UPDATES = {
    "800008": 2789.00,
    "7900862": 5770.00,
    "7900962": 8150.00,
    "VCB08": 79.90,
    "AR2064": 69.00,
    "40009": 2.85,
    "40010": 22.65,
    "40802": 16.00,
    "76026": 99.90,
    "90160": 149.90,
    "621103": 619.00,
    "772060": 211.90,
    "76050": 14.00,
    "40070": 8.70,
    "773322": 74.54,
    "787247": 379.00
}

async def apply_updates():
    print(f"🚀 Applicazione di {len(FINAL_UPDATES)} aggiornamenti prezzi e attivazione...")

    for sku, price in FINAL_UPDATES.items():
        print(f"\n📦 Elaborazione SKU: {sku}")
        
        # 1. Trova ID prodotto e variante via SKU
        query = f'query {{ products(first:1, query: "sku:{sku}") {{ nodes {{ id title variants(first: 1) {{ nodes {{ id }} }} }} }} }}'
        res = await shopify_request(query)
        
        products = res.get('data', {}).get('products', {}).get('nodes', [])
        if not products:
            print(f"   ⚠️ SKU {sku} non trovato su Shopify.")
            continue
            
        product = products[0]
        product_id = product['id']
        variant_id = product['variants']['nodes'][0]['id']
        
        # 2. Update Prezzo via productVariantsBulkUpdate
        price_mutation = """
        mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            product { id }
            productVariants { id price }
            userErrors { field message }
          }
        }
        """
        price_res = await shopify_request(price_mutation, {
            "productId": product_id,
            "variants": [{"id": variant_id, "price": str(price)}]
        })
        
        if price_res.get('data', {}).get('productVariantsBulkUpdate', {}).get('userErrors'):
            print(f"   ❌ Errore prezzo {product['title']}: {price_res['data']['productVariantsBulkUpdate']['userErrors']}")
        else:
            print(f"   💰 Prezzo aggiornato a {price} €")

        # 3. Update Status via productUpdate
        status_mutation = """
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id status }
            userErrors { field message }
          }
        }
        """
        status_res = await shopify_request(status_mutation, {
            "input": {"id": product_id, "status": "ACTIVE"}
        })
        
        if status_res.get('data', {}).get('productUpdate', {}).get('userErrors'):
            print(f"   ❌ Errore attivazione {product['title']}: {status_res['data']['productUpdate']['userErrors']}")
        else:
            print(f"   ✅ {product['title']} ora ATTIVO.")

    print("\n🎉 Operazione completata.")

if __name__ == "__main__":
    asyncio.run(apply_updates())
