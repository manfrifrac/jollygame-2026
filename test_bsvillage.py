import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import re

async def scrape_bsvillage():
    # SKU di prova
    skus = ["KITPROV6188WO", "WR000500", "74691"] # Piscina, Robot, Pompa
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        for sku in skus:
            print(f"🔍 Ricerca SKU su BSVillage: {sku}")
            try:
                # Usiamo la loro ricerca interna
                await page.goto(f"https://www.bsvillage.com/search?q={sku}", wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Cerchiamo il blocco prezzo
                price_elem = soup.select_one('.price, .actual-price, .special-price')
                if price_elem:
                    price = price_elem.get_text(strip=True)
                    print(f"   💰 Trovato: {price}")
                else:
                    # Se siamo finiti nella scheda prodotto direttamente
                    price_elem = soup.select_one('.product-price')
                    if price_elem:
                        print(f"   💰 Trovato (Scheda): {price_elem.get_text(strip=True)}")
                    else:
                        print("   ❌ Non trovato.")
            except Exception as e:
                print(f"   ⚠️ Errore: {e}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_bsvillage())
