import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import os

async def find_price_lists():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        targets = [
            "https://www.fluidra.it/cataloghi/",
            "https://www.grepool.com/it/documentazione"
        ]
        
        found_docs = []
        for url in targets:
            print(f"🔍 Cerco documenti in: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Cerchiamo link a PDF o XLS
                for a in soup.find_all('a', href=True):
                    href = a['href'].lower()
                    text = a.get_text(strip=True).lower()
                    if ".pdf" in href or ".xls" in href:
                        if any(x in href or x in text for x in ["prezzi", "listino", "tarifa", "catalogo", "2026", "2025"]):
                            full_url = a['href']
                            if not full_url.startswith('http'):
                                base = "https://www.fluidra.it" if "fluidra" in url else "https://www.grepool.com"
                                full_url = base + full_url
                            found_docs.append({"title": a.get_text(strip=True), "url": full_url})
            except Exception as e:
                print(f"   ❌ Errore su {url}: {e}")
                
        print(f"\n✅ Trovati {len(found_docs)} documenti potenzialmente interessanti:")
        for doc in found_docs:
            print(f"   📄 {doc['title']} -> {doc['url']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_price_lists())
