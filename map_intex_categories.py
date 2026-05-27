import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json
import sqlite3
from bs4 import BeautifulSoup

async def map_intex_categories():
    # Carichiamo gli URL dalla sitemap salvata
    import xml.etree.ElementTree as ET
    tree = ET.parse('intex_cat_sitemap.xml')
    root = tree.getroot()
    cat_urls = [loc.text for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    
    mapping = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        for url in cat_urls:
            print(f"Scansione categoria: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2) # Piccola attesa per rendering
                
                # Scrolling per caricare prodotti dinamici
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(1)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Estraiamo gli SKU presenti nella pagina
                # Intex usa spesso attributi data-product_sku o classi .sku
                skus = []
                # Cerco in vari posti comuni
                for item in soup.select('[data-product_sku], .sku, .product-sku'):
                    sku = item.get('data-product_sku') or item.get_text(strip=True)
                    if sku and len(sku) > 2:
                        skus.append(sku.strip())
                
                # Cerco anche i link ai prodotti che spesso contengono lo SKU nel titolo/alt
                for a in soup.select('a[href*="/prodotto/"]'):
                    # Qui non abbiamo lo SKU diretto, ma potremmo estrarre l'URL per il match
                    pass

                # Pulizia categoria (estratta dall'URL o breadcrumb)
                cat_name = url.replace("https://www.intexitalia.com/", "").strip("/")
                
                mapping[cat_name] = list(set(skus))
                print(f"   -> Trovati {len(skus)} SKU.")
                
            except Exception as e:
                print(f"   ❌ Errore su {url}: {e}")

        await browser.close()

    with open("intex_sku_category_map.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=4)
    
    print("\n✅ Mappatura SKU-Categoria completata.")

if __name__ == "__main__":
    asyncio.run(map_intex_categories())
