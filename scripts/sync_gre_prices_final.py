import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="jollygame-importer/jollygame-importer/.env")

# Configuration
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

async def get_lowest_price(page, url):
    print(f"🔎 Analizzando: {url}")
    try:
        await page.goto(url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(5000)

        # Bypass Cookiebot
        try:
            cookie_btn = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await page.wait_for_timeout(2000)
        except: pass

        # Clicca Acquista
        buy_btn = page.locator(".js-openModal, .where-to-buy button, button:has-text('Acquista')").first
        if await buy_btn.count() > 0:
            print("🖱️ Clic su pulsante Acquista...")
            await buy_btn.click(force=True)
            await page.wait_for_timeout(15000) # Attesa widget Netrivals

            # Estrazione prezzi
            prices_text = await page.evaluate('''() => {
                const res = [];
                document.querySelectorAll('*').forEach(el => {
                    const t = el.innerText;
                    if (t && t.includes('€') && t.length < 15 && /\\d/.test(t)) {
                        res.push(t.trim());
                    }
                });
                return [...new Set(res)];
            }''')
            
            print(f"💰 Prezzi trovati: {prices_text}")
            
            numeric = []
            for p in prices_text:
                clean = re.sub(r'[^\d,.]', '', p).replace(',', '.')
                try:
                    val = float(clean)
                    if val > 50: numeric.append(val)
                except: continue
            
            if numeric:
                return min(numeric)
        else:
            print("❌ Pulsante Acquista non trovato.")
    except Exception as e:
        print(f"❌ Errore scraping: {e}")
    return None

async def run_sync():
    # 1. Carica i prodotti mappati
    drafts_path = "jollygame-importer/jollygame-importer/gre_mapped_drafts_v6.json"
    if not os.path.exists(drafts_path):
        print("File draft non trovato.")
        return
    
    with open(drafts_path, 'r', encoding='utf-8') as f:
        drafts = json.load(f)

    # Prendiamo tutti quelli che hanno un gre_url valido
    to_process = [d for d in drafts if d.get('gre_url')]
    print(f"🚀 Trovati {len(to_process)} prodotti con URL mappato. Inizio elaborazione...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        for prod in to_process:
            sku = prod.get('sku')
            url = prod['gre_url']
            print(f"\n🚀 Sincronizzazione {prod['title']} (SKU {sku})...")

            price = await get_lowest_price(page, url)
            if price:
                print(f"✨ Nuovo prezzo per {prod['title']}: {price} €")
                
                # Fetch variant ID
                get_id_query = f'query {{ product(id: "{prod["id"]}") {{ variants(first: 1) {{ nodes {{ id }} }} }} }}'
                id_res = await shopify_request(get_id_query)
                
                try:
                    variant_id = id_res['data']['product']['variants']['nodes'][0]['id']
                    
                    input_data = {
                        "id": prod["id"],
                        "status": "ACTIVE", # Proviamo sempre a portarlo online se troviamo il prezzo
                        "variants": [{"id": variant_id, "price": str(price)}]
                    }
                    
                    mutation = """
                    mutation productUpdate($input: ProductInput!) {
                      productUpdate(input: $input) {
                        product { id status }
                        userErrors { message }
                      }
                    }
                    """
                    update_res = await shopify_request(mutation, {"input": input_data})
                    if update_res.get('data', {}).get('productUpdate', {}).get('userErrors'):
                        print(f"❌ Errore aggiornamento: {update_res['data']['productUpdate']['userErrors']}")
                    else:
                        print(f"✅ Prodotto {prod['title']} ONLINE con prezzo {price} €")
                except:
                    print(f"⚠️ Errore nel recupero dati Shopify per {prod['title']}")
            else:
                print(f"⚠️ Impossibile determinare il prezzo per SKU {sku}")

        await browser.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_sync())
