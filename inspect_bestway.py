import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup

async def inspect_bestway():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        # Assicuriamoci che la directory esista
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
            
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        url = "https://it.bestway.eu/"
        print(f"Navigating to: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000) # Attesa extra per JS
            
            # Screenshot della home
            await page.screenshot(path="debug_bestway_home.png", full_page=False)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # 1. Analisi Menu Categorie
            print("\n--- Analisi Menu Categorie ---")
            # Spesso i siti hanno menu con classi come 'nav', 'menu', 'categories'
            nav_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)
                # Filtriamo link che sembrano categorie (es. contengono 'categorie' o sono nel menu)
                if any(x in href for x in ["/piscine", "/idromassaggio", "/sport", "/tempo-libero", "/articoli-mare"]):
                    nav_links.append({"text": text, "url": href})
            
            unique_nav = {l['url']: l for l in nav_links}.values()
            for l in unique_nav:
                print(f"Categoria: {l['text']} -> {l['url']}")

            # 2. Identificazione potenziale struttura prodotti
            # Cerchiamo di capire se è Magento (.product-item), Shopify, o altro
            print("\n--- Analisi Struttura Pagina ---")
            if soup.select(".product-item"): print("Rilevato pattern Magento (.product-item)")
            elif soup.select(".product-card"): print("Rilevato pattern .product-card")
            else:
                # Stampiamo le classi dei primi 5 div per avere un'idea
                for div in soup.find_all('div', class_=True)[:10]:
                    print(f"Div class: {div['class']}")

            with open("debug_bestway_home.html", "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"Errore durante l'ispezione: {e}")
        finally:
            await browser_context.close()

if __name__ == "__main__":
    asyncio.run(inspect_bestway())
