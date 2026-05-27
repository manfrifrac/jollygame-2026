import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re

async def get_market_prices():
    # SKU di prova (Top Seller Fluidra/Zodiac)
    skus = ["WR000166", "R0516700", "74691", "KIT500GY"] # Robot, Ricambio, Pompa, Piscina
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        results = {}
        for sku in skus:
            # Cerchiamo su un grande aggregatore/distributore
            search_url = f"https://www.google.com/search?q={sku}+prezzo+piscina"
            print(f"🔍 Cerco prezzo per SKU: {sku}")
            try:
                await page.goto(search_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                content = await page.content()
                # Cerchiamo pattern tipo "1.234,00 €" o "€ 1.234"
                prices = re.findall(r'(\d+[\.,]\d{2})\s*€|€\s*(\d+[\.,]\d{2})', content)
                
                if prices:
                    # Pulizia e selezione del prezzo più basso/comune
                    valid_prices = []
                    for p_match in prices:
                        val = p_match[0] if p_match[0] else p_match[1]
                        valid_prices.append(float(val.replace('.', '').replace(',', '.')))
                    
                    if valid_prices:
                        best_price = min(valid_prices)
                        results[sku] = best_price
                        print(f"   💰 Prezzo trovato: {best_price} €")
                else:
                    print("   ❌ Nessun prezzo trovato.")
                    
            except Exception as e:
                print(f"   ⚠️ Errore: {e}")

        await browser.close()
    return results

if __name__ == "__main__":
    asyncio.run(get_market_prices())
