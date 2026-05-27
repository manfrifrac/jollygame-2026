import asyncio
import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="jollygame-importer/jollygame-importer/.env")

SHOP_DOMAIN = os.getenv("SHOP_DOMAIN")
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

async def apply_gre_updates():
    report_path = "gre_price_update_report.json"
    if not os.path.exists(report_path):
        print("Report non trovato.")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    updates = report['updates']
    print(f"🚀 Applicazione di {len(updates)} aggiornamenti prezzi Gre...")

    count = 0
    # Group by product_id to use bulk update effectively (Shopify accepts multiple variants per call)
    product_map = {}
    for u in updates:
        pid = u['product_id']
        if pid not in product_map:
            product_map[pid] = []
        product_map[pid].append(u)

    for pid, variants_to_update in product_map.items():
        # 1. Update Prices
        price_mutation = """
        mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            product { id }
            userErrors { field message }
          }
        }
        """
        variant_inputs = [{"id": v['variant_id'], "price": v['new_price']} for v in variants_to_update]
        
        await shopify_request(price_mutation, {
            "productId": pid,
            "variants": variant_inputs
        })

        # 2. Update Status to ACTIVE and inventoryPolicy to CONTINUE
        # We use productUpdate for status
        status_mutation = """
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id status }
            userErrors { message }
          }
        }
        """
        await shopify_request(status_mutation, {
            "input": {"id": pid, "status": "ACTIVE"}
        })
        
        # Also need to set inventoryPolicy: CONTINUE for each variant to ensure availability
        # Reuse productVariantsBulkUpdate for policy
        policy_inputs = [{"id": v['variant_id'], "inventoryPolicy": "CONTINUE"} for v in variants_to_update]
        await shopify_request(price_mutation, {
            "productId": pid,
            "variants": policy_inputs
        })

        count += len(variants_to_update)
        if count % 50 == 0 or count == len(updates):
            print(f"   - Elaborati {count} / {len(updates)} prodotti...")

    print(f"\n✅ Sincronizzazione Listino Gre completata!")

if __name__ == "__main__":
    asyncio.run(apply_gre_updates())
