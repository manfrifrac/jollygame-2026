import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import re
import os

async def search_market_prices():
    # Carica i prodotti che mancano ancora
    if not os.path.exists("gre_mapped_drafts_v6.json"):
        print("File gre_mapped_drafts_v6.json non trovato.")
        return

    with open("gre_mapped_drafts_v6.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    # Filtra quelli senza URL o con URL falliti
    to_search = [p for p in products if not p.get('gre_url') and p.get('sku')]
    print(f"🔍 Ricerca prezzi di mercato per {len(to_search)} prodotti su Google/Shopping...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        for prod in to_search[:15]: # Test sui primi 15
            sku = prod['sku']
            query = f"prezzo Gre {sku} {prod['title']}"
            print(f"\n🔎 Cerco: {query}")
            
            try:
                # Usiamo Google Shopping o Ricerca generica
                await page.goto(f"https://www.google.it/search?q={query.replace(' ', '+')}&tbm=shop", wait_until="load")
                await page.wait_for_timeout(3000)
                
                # Gestione eventuale consenso Google
                if "consent.google" in page.url:
                    try:
                        btn = page.locator("button:has-text('Accetto tutto'), button:has-text('Accept all')").first
                        if await btn.count() > 0:
                            await btn.click()
                            await page.wait_for_timeout(2000)
                    except: pass

                # Estrazione prezzi da Google Shopping
                prices = await page.evaluate('''() => {
                    const found = [];
                    // Selettori comuni per i prezzi in Google Shopping
                    document.querySelectorAll('.a8a15, .HST3n, .T14X9c, span[price]').forEach(el => {
                        const t = el.innerText;
                        if (t && t.includes('€')) found.push(t);
                    });
                    // Backup: cerca in tutto il testo
                    if (found.length === 0) {
                         document.querySelectorAll('span, b, div').forEach(el => {
                            const t = el.innerText;
                            if (t && t.includes('€') && t.length < 15 && /\\d/.test(t)) found.push(t);
                         });
                    }
                    return [...new Set(found)];
                }''')

                print(f"💰 Trovati: {prices}")
                
                numeric = []
                for p_text in prices:
                    clean = re.sub(r'[^\d,.]', '', p_text).replace(',', '.')
                    try:
                        val = float(clean)
                        if val > 1: numeric.append(val)
                    except: continue

                if numeric:
                    min_price = min(numeric)
                    print(f"✅ Minimo: {min_price} €")
                    prod['market_price'] = min_price
                    prod['price_source'] = "Google Shopping"
                else:
                    print("❌ Nessun prezzo trovato.")

            except Exception as e:
                print(f"❌ Errore: {e}")

        await browser.close()

    with open("gre_market_prices_final.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)
    
    print("\n✅ Ricerca completata.")

if __name__ == "__main__":
    asyncio.run(search_market_prices())
