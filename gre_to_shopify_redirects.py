
import asyncio
import pandas as pd
import shopify
from playwright.async_api import async_playwright
import base64
import re
import urllib.parse

# CONFIGURAZIONE SHOPIFY
SHOP_URL = "jollygamepiscine.myshopify.com"
ACCESS_TOKEN = "shptka_56c35907b97a4928db981b5c8f926324"

# Inizializza Shopify API
shopify.ShopifyResource.set_site(f"https://{SHOP_URL}/admin/api/2024-01")
shopify.ShopifyResource.set_headers({"X-Shopify-Access-Token": ACCESS_TOKEN})

def decrypt_netrivals_url(encoded_str):
    """Decripta l'URL di Jolly Game dai link Netrivals di Grepool."""
    try:
        # Step 1: Prima decodifica Base64
        decoded_bytes = base64.b64decode(encoded_str)
        step1 = decoded_bytes.decode('utf-8', errors='ignore')
        
        # Step 2: Rimozione rumore (Netrivals inserisce 4 caratteri alla posizione 12)
        # Esempio: aHR0cHM6Ly93 xVbd 3cuam9sbHlnYW1lL...
        if len(step1) > 16:
            clean_b64 = step1[:12] + step1[16:]
            # Step 3: Seconda decodifica Base64
            final_url = base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
            return final_url
    except Exception as e:
        print(f"Errore decriptazione: {e}")
    return None

async def get_shopify_variant_data(sku):
    """Trova l'handle del prodotto e l'ID della variante su Shopify tramite SKU."""
    sku_clean = sku.strip().upper()
    try:
        # Ricerca diretta via SKU (più affidabile)
        products = shopify.Product.find(query=f"sku:{sku_clean}")
        if not products:
            # Fallback: ricerca manuale nei prodotti recenti
            products = shopify.Product.find(limit=50)
            
        for product in products:
            for variant in product.variants:
                if variant.sku and variant.sku.strip().upper() == sku_clean:
                    return {"handle": product.handle, "variant_id": variant.id, "title": product.title}
    except: pass
    return None

async def process_product(page, url):
    """Estrae SKU, apre modale, decripta link e mappa su Shopify."""
    print(f"Analizzo: {url}")
    try:
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)
        
        # 1. Estrazione SKU
        sku = await page.evaluate('''() => {
            const text = document.body.innerText;
            const match = text.match(/Rif\.:?\s*([A-Z0-9]{5,})/i) || 
                          text.match(/Ref\.:?\s*([A-Z0-9]{5,})/i);
            return match ? match[1].trim() : null;
        }''')
        if not sku: return None
        
        # 2. Click pulsante Acquista per caricare la modale Netrivals
        buy_btn = page.locator("text=/Acquista/i").first
        if await buy_btn.is_visible():
            await buy_btn.click()
            await page.wait_for_timeout(5000)
            
            # 3. Estrazione link Netrivals per Jolly Game
            netrivals_data = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                const jolly_link = links.find(a => a.href.includes('storename=jollygame'));
                if (jolly_link) {
                    const urlParams = new URLSearchParams(jolly_link.href.split('?')[1]);
                    return urlParams.get('store-redirect-url');
                }
                return null;
            }''')
            
            if netrivals_data:
                old_url = decrypt_netrivals_url(netrivals_data)
                if old_url:
                    print(f"  [OK] Link Decriptato: {old_url}")
                    # 4. Match Shopify
                    shopify_info = await get_shopify_variant_data(sku)
                    if shopify_info:
                        return {
                            "Redirect from": old_url.replace("https://jollygame.it", ""),
                            "Redirect to": f"/products/{shopify_info['handle']}?variant={shopify_info['variant_id']}",
                            "SKU": sku,
                            "Title": shopify_info['title']
                        }
                    else:
                        print(f"  [!] SKU {sku} non trovato su Shopify.")
            else:
                print(f"  [!] Link Netrivals non trovato per {sku}")
    except Exception as e:
        print(f"  Errore: {e}")
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--no-sandbox'])
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        page = await context.new_page()
        
        # Categorie da scansionare
        categories = [
            "https://www.grepool.com/it/piscine-in-acciaio",
            "https://www.grepool.com/it/piscine-interrate"
        ]
        
        all_results = []
        for cat_url in categories:
            print(f"\nEsploro Categoria: {cat_url}")
            await page.goto(cat_url, wait_until='networkidle')
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll("a"))
                    .map(a => a.href)
                    .filter(href => href.includes("/it/") && href.split("/").length > 5);
            }''')
            
            for p_url in sorted(list(set(links)))[:20]: # Test su 20 prodotti
                res = await process_product(page, p_url)
                if res: all_results.append(res)
        
        if all_results:
            df = pd.DataFrame(all_results)
            df.to_csv("redirects_gre_netrivals.csv", index=False)
            print(f"\nCOMPLETATO! {len(all_results)} redirect salvati in redirects_gre_netrivals.csv")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
