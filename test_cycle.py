
import asyncio
import pandas as pd
import shopify
from playwright.async_api import async_playwright
import base64
import re

# CONFIGURAZIONE SHOPIFY
SHOP_URL = "jollygamepiscine.myshopify.com"
ACCESS_TOKEN = "shptka_56c35907b97a4928db981b5c8f926324"

shopify.ShopifyResource.set_site(f"https://{SHOP_URL}/admin/api/2024-01")
shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": ACCESS_TOKEN})

def decrypt_url(encoded_str):
    try:
        step1 = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        if len(step1) > 16:
            clean_b64 = step1[:12] + step1[16:]
            final_url = base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
            return final_url
    except: pass
    return None

async def get_shopify_data(sku):
    try:
        products = shopify.Product.find(query=f"sku:{sku}")
        if products:
            for v in products[0].variants:
                if v.sku.strip().upper() == sku.strip().upper():
                    return {"handle": products[0].handle, "variant_id": v.id}
    except: pass
    return None

async def test_cycle():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--no-sandbox'])
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        page = await context.new_page()
        
        # Test su 2 URL reali e sicuri
        test_urls = [
            "https://www.grepool.com/it/piscine-interrate/sumatra-ovale/500-x-300-x-120-cm-4",
            "https://www.grepool.com/it/piscine-in-acciaio/amazonia-ovale/610-x-375-x-132-cm-3"
        ]
        
        results = []
        for url in test_urls:
            print(f"\n--- TEST SU: {url} ---")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(5000)
            
            # Estrazione SKU e Link Netrivals
            data = await page.evaluate('''() => {
                const text = document.body.innerText;
                const skuMatch = text.match(/Rif\.:?\s*([A-Z0-9]{5,})/i) || text.match(/Ref\.:?\s*([A-Z0-9]{5,})/i);
                const sku = skuMatch ? skuMatch[1].trim() : null;
                
                const jolly_link = Array.from(document.querySelectorAll("a[href*='netrivals.com']"))
                    .find(a => a.href.includes('storename=jollygame'));
                
                let encoded = null;
                if (jolly_link) {
                    const params = new URLSearchParams(jolly_link.href.split('?')[1]);
                    encoded = params.get('store-redirect-url');
                }
                return { sku, encoded };
            }''')
            
            print(f"SKU estratto: {data['sku']}")
            if data['encoded']:
                old_url = decrypt_url(data['encoded'])
                print(f"URL Originale Decriptato: {old_url}")
                
                if data['sku']:
                    shopify_info = await get_shopify_data(data['sku'])
                    if shopify_info:
                        print(f"Match Shopify trovato: /products/{shopify_info['handle']}?variant={shopify_info['variant_id']}")
                        results.append({
                            "Redirect from": old_url.replace("https://jollygame.it", ""),
                            "Redirect to": f"/products/{shopify_info['handle']}?variant={shopify_info['variant_id']}",
                            "SKU": data['sku']
                        })
                    else:
                        print(f"SKU {data['sku']} non trovato su Shopify.")
            else:
                print("Link Netrivals NON TROVATO (forse il widget non si è caricato).")
        
        if results:
            df = pd.DataFrame(results)
            df.to_csv("test_redirect_result.csv", index=False)
            print(f"\nTEST COMPLETATO: {len(results)} match validati.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cycle())
