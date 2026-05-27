import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import re

async def scrape_google_shopping():
    # Esempi reali
    skus = ["WR000500", "26378NP", "KITPROV6188WO"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        for sku in skus:
            print(f"🔍 Google Shopping SKU: {sku}")
            try:
                # Tab Shopping di Google
                url = f"https://www.google.com/search?q={sku}&tbm=shop"
                await page.goto(url, wait_until="networkidle")
                await page.wait_for_timeout(5000)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Cerchiamo i prezzi nelle classi comuni di Google Shopping
                # Spesso sono dentro span con classi come 'a83A0c' o testi che finiscono con '€'
                prices = []
                for span in soup.find_all(['span', 'div', 'b']):
                    text = span.get_text(strip=True)
                    if '€' in text and len(text) < 15:
                        # Pulizia prezzo
                        match = re.search(r'([\d.,]+)', text)
                        if match:
                            val = match.group(1).replace('.', '').replace(',', '.')
                            try: prices.append(float(val))
                            except: pass
                
                if prices:
                    best = min(prices)
                    print(f"   💰 Prezzi trovati: {list(set(prices))}")
                    print(f"   🎯 Miglior Prezzo (Min): {best} €")
                else:
                    print("   ❌ Nessun prezzo trovato in Shopping.")
                    
            except Exception as e:
                print(f"   ⚠️ Errore: {e}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_google_shopping())
