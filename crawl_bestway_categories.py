import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup

async def crawl_bestway_structure():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print("Mappatura completa del sito Bestway...")
        await page.goto("https://it.bestway.eu/", wait_until="networkidle")
        
        # Apriamo tutti i menu se necessario o leggiamo l'HTML completo
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        category_links = set()
        product_links = set()
        
        # Estraiamo tutti i link dal menu e dal footer
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Se è un link interno
            if href.startswith("/") or "it.bestway.eu" in href:
                full_url = href if href.startswith("http") else f"https://it.bestway.eu{href}"
                
                if "/catalog/" in full_url:
                    category_links.add(full_url)
                elif "/p/" in full_url:
                    product_links.add(full_url)
        
        print(f"Trovate {len(category_links)} macro-categorie.")
        
        # Scendiamo di un livello nelle macro-categorie per trovare sottocategorie
        all_sub_categories = list(category_links)
        for cat in list(category_links)[:10]: # Testiamo le prime 10
            print(f"Esploro sottocategorie di: {cat}")
            try:
                await page.goto(cat, wait_until="networkidle")
                sub_content = await page.content()
                sub_soup = BeautifulSoup(sub_content, 'lxml')
                for a in sub_soup.find_all('a', href=True):
                    h = a['href']
                    if "/catalog/" in h:
                        f_url = h if h.startswith("http") else f"https://it.bestway.eu{h}"
                        all_sub_categories.append(f_url)
            except:
                continue
        
        final_categories = list(set(all_sub_categories))
        print(f"Totale categorie e sottocategorie individuate: {len(final_categories)}")
        
        with open("bestway_discovered_categories.json", "w") as f:
            import json
            json.dump(final_categories, f, indent=4)
            
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(crawl_bestway_structure())
