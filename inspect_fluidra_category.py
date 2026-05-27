import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
from bs4 import BeautifulSoup

async def inspect_category(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        print(f"Avvio Chrome REALE con profilo: {user_data_dir}")
        
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            print("1. Passaggio dalla Home per validare la sessione...")
            await page.goto("https://pro.fluidra.com/it_it/", wait_until="load", timeout=60000)
            await page.wait_for_timeout(5000)
            
            h_content = await page.content()
            is_logged_in_h = "log out" in h_content.lower() or "esci" in h_content.lower() or "mio account" in h_content.lower()
            print(f"Stato Login in Home: {is_logged_in_h}")

            print(f"2. Navigazione verso la categoria: {url}")
            await page.goto(url, wait_until="load", timeout=90000)
            
            print("Attendo 15 secondi per il caricamento della griglia prodotti...")
            await page.wait_for_timeout(15000)
            
            # Movimenti e click per simulare attività
            await page.mouse.move(random.randint(200, 800), random.randint(200, 800))
            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(3000)
            await page.mouse.wheel(0, -400)
            
            content = await page.content()
            
            # Verifica SKU specifica
            if "12508-1" in content:
                print("TROVATO! Lo SKU 12508-1 è presente nell'HTML.")
            else:
                print("SKU 12508-1 non trovato.")
            
            # Salvataggio HTML per ispezione
            with open("debug_real_chrome_v3.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            soup = BeautifulSoup(content, 'lxml')
            links = soup.select("a.product-item-link")
            print(f"Link con classe .product-item-link trovati: {len(links)}")
            for l in links:
                print(f"LINK: {l['href']}")
            
            # Se zero, proviamo a cercare i div che hai indicato tu
            inners = soup.select(".product-item-info")
            print(f"Div con classe .product-item-info trovati: {len(inners)}")
            
            await page.screenshot(path="debug_real_chrome_v3.png", full_page=True)
            print("Screenshot salvato: debug_real_chrome_v3.png")

        except Exception as e:
            print(f"Errore: {e}")
        finally:
            await browser_context.close()

if __name__ == "__main__":
    target_url = "https://pro.fluidra.com/it_it/catalog/category/view/s/piscine-in-acciaio/id/50310/"
    asyncio.run(inspect_category(target_url))
