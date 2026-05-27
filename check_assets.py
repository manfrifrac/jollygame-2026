import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup

async def final_check_assets(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True, # Usiamo headless ora che sappiamo che il login funziona
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)
        
        print(f"Controllo asset per: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(10000)
        
        # Scorriamo tutto per caricare documenti pigri
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        print("\n--- PDF TROVATI ---")
        for a in soup.find_all('a', href=True):
            if ".pdf" in a['href'].lower():
                print(f"PDF: {a['href']}")
                
        print("\n--- IMMAGINI TROVATE ---")
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and "placeholder" not in src:
                print(f"IMG: {src}")

        await browser_context.close()

if __name__ == "__main__":
    test_url = "https://pro.fluidra.com/it_it/1168796-kit-50pz-vite-autof-inox-d-3-9-x-9-5.html"
    asyncio.run(final_check_assets(test_url))
