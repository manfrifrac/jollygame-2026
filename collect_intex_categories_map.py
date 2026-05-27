import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json
from bs4 import BeautifulSoup

async def collect_intex_categories():
    async with async_playwright() as p:
        # Usiamo headless=False per permettere la risoluzione manuale di eventuali CAPTCHA
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print("🚀 Apertura pagina categorie Intex Italia...")
        await page.goto("https://www.intexitalia.com/prodotti/", wait_until="networkidle", timeout=60000)
        
        # Diamo tempo all'utente di risolvere eventuali captcha o cookie
        print("ℹ️  Se vedi un CAPTCHA, risolvilo nel browser. Hai 30 secondi...")
        await page.wait_for_timeout(30000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        # Cerchiamo le macro-categorie
        cat_links = []
        # Il selettore potrebbe essere .list-categories .item a
        items = soup.select('.list-categories .item a, .list-product-categories a')
        for a in items:
            href = a['href']
            if "/prodotti/" in href and href != "https://www.intexitalia.com/prodotti/":
                cat_links.append({
                    "name": a.get_text(strip=True),
                    "url": href
                })
        
        print(f"✅ Trovate {len(cat_links)} macro-categorie.")
        
        category_map = {}
        
        for cat in cat_links:
            print(f"📂 Esplorazione categoria: {cat['name']}...")
            await page.goto(cat['url'], wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # Scrolling per caricare tutti i prodotti (se c'è lazy loading)
            for _ in range(5):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(1000)
            
            cat_content = await page.content()
            cat_soup = BeautifulSoup(cat_content, 'lxml')
            
            # Cerchiamo i link ai prodotti
            prod_links = []
            # Selettore prodotti standard
            links = cat_soup.select('.product-item a[href*="/prodotto/"], .item-product a[href*="/prodotto/"]')
            for l in links:
                prod_links.append(l['href'].split('?')[0])
            
            # Rimozione duplicati
            prod_links = list(set(prod_links))
            category_map[cat['name']] = prod_links
            print(f"   -> Trovati {len(prod_links)} prodotti.")

        # Salvataggio
        with open("intex_categories_mapping.json", "w", encoding="utf-8") as f:
            json.dump(category_map, f, indent=4)
        
        print("\n🎉 Mappatura completata! File salvato: intex_categories_mapping.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(collect_intex_categories())
