
import asyncio
import pandas as pd
import shopify
from playwright.async_api import async_playwright
import base64
import re
import os

# CONFIGURAZIONE SHOPIFY
SHOP_URL = "jollygamepiscine.myshopify.com"
ACCESS_TOKEN = "shptka_56c35907b97a4928db981b5c8f926324"

shopify.ShopifyResource.set_site(f"https://{SHOP_URL}/admin/api/2024-01")
shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": ACCESS_TOKEN})

def decrypt_url(encoded_str):
    """Logica di decriptazione Netrivals: Base64 -> Remove 4 chars at index 12 -> Base64."""
    try:
        step1 = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        if len(step1) > 16:
            # Rimuove i 4 caratteri di disturbo inseriti da Netrivals
            clean_b64 = step1[:12] + step1[16:]
            final_url = base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
            return final_url
    except: pass
    return None

async def get_shopify_data(sku):
    """Mappa lo SKU all'handle e ID variante su Shopify."""
    try:
        products = shopify.Product.find(query=f"sku:{sku}")
        if products:
            for v in products[0].variants:
                if v.sku.strip().upper() == sku.strip().upper():
                    return {"handle": products[0].handle, "variant_id": v.id}
    except: pass
    return None

async def scrape_all_gre():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--no-sandbox'])
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        page = await context.new_page()
        
        categories = [
            "https://www.grepool.com/it/piscine-in-acciaio",
            "https://www.grepool.com/it/piscine-interrate",
            "https://www.grepool.com/it/piscine-in-legno"
        ]
        
        results = []
        for cat in categories:
            print(f"Scansione categoria: {cat}")
            await page.goto(cat, wait_until='networkidle')
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll("a"))
                    .map(a => a.href)
                    .filter(href => href.includes("/it/") && href.split("/").length > 5);
            }''')
            
            unique_links = sorted(list(set(links)))
            for url in unique_links:
                print(f"  Elaborazione: {url}")
                try:
                    await page.goto(url, wait_until='networkidle')
                    await page.wait_for_timeout(5000)
                    
                    # Estrai SKU e Link Netrivals
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
                    
                    if data['sku'] and data['encoded']:
                        old_url = decrypt_url(data['encoded'])
                        if old_url:
                            shopify_info = await get_shopify_data(data['sku'])
                            if shopify_info:
                                print(f"    [SUCCESS] Mappato: {data['sku']}")
                                results.append({
                                    "Redirect from": old_url.replace("https://jollygame.it", ""),
                                    "Redirect to": f"/products/{shopify_info['handle']}?variant={shopify_info['variant_id']}",
                                    "SKU": data['sku']
                                })
                except Exception as e:
                    print(f"    Errore su {url}: {e}")
        
        if results:
            df = pd.DataFrame(results)
            df.to_csv("redirects_finali_grepool.csv", index=False)
            print(f"\nGenerato CSV con {len(results)} redirect.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_all_gre())
