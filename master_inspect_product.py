import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup
import json
import re

async def master_inspect(url):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        print(f"Avvio Master Inspection con profilo: {user_data_dir}")

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
            print(f"Navigazione verso: {url}")
            await page.goto(url, wait_until="load", timeout=90000)
            print("Pagina caricata. Aspetto 15 secondi per popolamento totale...")
            await page.wait_for_timeout(15000)

            # Scroll profondo e ritorno su per attivare tutto
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)

            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')

            # --- ESTRAZIONE DATI ---
            results = {
                "url": url,
                "h1_tags": [h.get_text(strip=True) for h in soup.find_all('h1')],
                "h2_tags": [h.get_text(strip=True) for h in soup.find_all('h2')],
                "all_skus": re.findall(r'SKU[:\s]+([A-Z0-9-]+)', content, re.IGNORECASE),
                "data_attributes": [],
                "json_ld": []
            }

            # Cerca attributi data-sku ovunque
            for tag in soup.find_all(True):
                if tag.has_attr('data-sku'):
                    results['data_attributes'].append(f"data-sku: {tag['data-sku']}")
                if tag.has_attr('data-product-sku'):
                    results['data_attributes'].append(f"data-product-sku: {tag['data-product-sku']}")

            # Estrai JSON-LD (MOLTO IMPORTANTE)
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    results['json_ld'].append(json.loads(script.string))
                except:
                    pass

            # Cerca tabelle tecniche
            results['tables'] = []
            for table in soup.find_all('table'):
                results['tables'].append(table.get_text(separator=" | ", strip=True)[:500])

            print("\n--- RISULTATI MASTER INSPECTION ---")
            print(f"H1 trovati: {results['h1_tags']}")
            print(f"SKU trovati nei pattern: {results['all_skus']}")
            print(f"JSON-LD trovati: {len(results['json_ld'])}")
            
            # Se troviamo JSON-LD, estraiamo i dati da lì
            for ld in results['json_ld']:
                if isinstance(ld, dict):
                    if ld.get('@type') == 'Product' or '@graph' in ld:
                        print("Trovato blocco Prodotto nel JSON-LD!")
                        # Spesso i dati sono qui

            with open("master_product_debug.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

            await page.screenshot(path="master_debug.png", full_page=True)
            print("\nIspezione completata. Controlla master_product_debug.json")

        except Exception as e:
            print(f"Errore: {e}")
        finally:
            print("Chiudo il browser...")
            await browser_context.close()

if __name__ == "__main__":
    test_url = "https://pro.fluidra.com/it_it/1168796-kit-50pz-vite-autof-inox-d-3-9-x-9-5.html"
    asyncio.run(master_inspect(test_url))
