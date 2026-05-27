import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup
import json

async def inspect_bestway_product(url):
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
        
        print(f"Navigating to product: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # Estrazione dati
            data = {}
            
            # Titolo
            title_elem = soup.select_one("h1")
            data['title'] = title_elem.get_text(strip=True) if title_elem else "N/A"
            
            # Codice Prodotto / SKU (spesso vicino al titolo o in tabella)
            sku_elem = soup.find(text=lambda x: x and ("Codice" in x or "SKU" in x))
            data['sku'] = sku_elem.parent.get_text(strip=True) if sku_elem else "N/A"
            
            # Prezzo
            price_elem = soup.select_one("[class*='price'], [class*='Price']")
            data['price'] = price_elem.get_text(strip=True) if price_elem else "N/A"
            
            # EAN (Cerchiamo nel testo o in script JSON-LD)
            ean_search = soup.find(text=lambda x: x and "EAN" in x)
            data['ean'] = ean_search.parent.get_text(strip=True) if ean_search else "N/A"
            
            # Proviamo a cercare JSON-LD che spesso contiene EAN e SKU in modo pulito
            json_ld = soup.find_all("script", type="application/ld+json")
            data['json_ld_found'] = len(json_ld)
            for script in json_ld:
                try:
                    js_data = json.loads(script.string)
                    if js_data.get("@type") == "Product":
                        data['ean_json_ld'] = js_data.get("gtin13") or js_data.get("mpn") or js_data.get("sku")
                        data['sku_json_ld'] = js_data.get("sku")
                except:
                    pass

            # Immagini
            images = [img['src'] for img in soup.select("img") if "product" in img.get('src', '').lower() or "bestway" in img.get('src', '').lower()]
            data['images_count'] = len(images)
            data['first_image'] = images[0] if images else "N/A"

            print("\n--- Dati Estratti ---")
            for k, v in data.items():
                print(f"{k}: {v}")

            await page.screenshot(path="debug_bestway_product.png", full_page=True)
            with open("debug_bestway_product.html", "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"Errore: {e}")
        finally:
            await browser_context.close()

if __name__ == "__main__":
    target = "https://it.bestway.eu/p/piscina-gonfiabile-fast-set-183x51-cm"
    asyncio.run(inspect_bestway_product(target))
