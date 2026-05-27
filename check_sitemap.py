import asyncio
from playwright.async_api import async_playwright
import re

async def check_sitemap():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Spesso la sitemap principale punta ad altre sitemap
        sitemaps = ["https://it.bestway.eu/sitemap.xml", "https://it.bestway.eu/sitemap_index.xml"]
        
        all_product_links = []
        
        for sm in sitemaps:
            print(f"Controllo sitemap: {sm}")
            try:
                await page.goto(sm)
                content = await page.content()
                
                # Cerchiamo link che contengono /p/ (prodotti)
                links = re.findall(r'https://it\.bestway\.eu/p/[a-zA-Z0-9\-_]+', content)
                all_product_links.extend(links)
                
                # Se è un indice di sitemap, cerchiamo altre sitemap
                sub_sitemaps = re.findall(r'https://it\.bestway\.eu/sitemap_[a-zA-Z0-9\-_]+\.xml', content)
                for ssm in sub_sitemaps:
                    if ssm != sm:
                        print(f"Controllo sottomappa: {ssm}")
                        await page.goto(ssm)
                        sub_content = await page.content()
                        all_product_links.extend(re.findall(r'https://it\.bestway\.eu/p/[a-zA-Z0-9\-_]+', sub_content))
            except:
                continue
        
        unique_links = list(set(all_product_links))
        print(f"\nTotale prodotti unici trovati nella sitemap: {len(unique_links)}")
        
        if len(unique_links) > 0:
            with open("bestway_all_links.json", "w") as f:
                import json
                json.dump(unique_links, f, indent=4)
            print("Link salvati in bestway_all_links.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_sitemap())
