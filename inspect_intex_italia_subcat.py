import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup

async def inspect_intex_subcat(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"Navigating to category: {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        # Cerco sottocategorie
        subcats = soup.select('.list-categories .item a, .subcategories a, .category-item a')
        print(f"\n--- Sottocategorie trovate: {len(subcats)} ---")
        for s in subcats:
            print(f"Subcat: {s.get_text(strip=True)} -> {s['href']}")
            
        # Cerco i prodotti in questa pagina per capire se siamo a livello foglia
        products = soup.select('.product-item, .item-product, .product-card')
        print(f"\n--- Prodotti trovati in questa pagina: {len(products)} ---")
        
        await page.screenshot(path="intex_italia_subcat_debug.png")
        await browser.close()

if __name__ == "__main__":
    # Test su Piscine Fuori Terra
    target = "https://www.intexitalia.com/prodotti/piscine-fuori-terra/"
    asyncio.run(inspect_intex_subcat(target))
