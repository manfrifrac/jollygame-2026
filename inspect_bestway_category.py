import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup

async def inspect_bestway_category(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print(f"Navigating to category: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Scorriamo per caricare eventuali prodotti lazy-loaded
            for i in range(5):
                await page.mouse.wheel(0, 2000)
                await page.wait_for_timeout(1000)
            
            # Vediamo se c'è un pulsante "Carica Altri"
            load_more = await page.query_selector("button:has-text('Carica altri'), button:has-text('Mostra altri')")
            if load_more:
                print("Pulsante 'Carica altri' trovato!")
            
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # Cerchiamo i link ai prodotti (/p/)
            product_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith("/p/"):
                    product_links.append(href)
            
            unique_products = list(set(product_links))
            print(f"Trovati {len(unique_products)} link prodotti unici.")
            for link in unique_products[:10]:
                print(f"Prodotto: https://it.bestway.eu{link}")

            await page.screenshot(path="debug_bestway_category.png", full_page=True)
            with open("debug_bestway_category.html", "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"Errore: {e}")
        finally:
            await browser_context.close()

if __name__ == "__main__":
    target = "https://it.bestway.eu/catalog/piscine-fuori-terra"
    asyncio.run(inspect_bestway_category(target))
