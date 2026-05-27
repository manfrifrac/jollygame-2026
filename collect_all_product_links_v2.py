import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
from bs4 import BeautifulSoup
import json

async def collect_links():
    # Carichiamo le categorie (lista di dict)
    with open("fluidra_categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    # File per i risultati intermedi
    output_file = "fluidra_product_links_map.json"
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            all_products = json.load(f)
    else:
        all_products = {}

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = browser_context.pages[0]
        await Stealth().apply_stealth_async(page)

        # Elaboriamo 20 categorie alla volta per sessione
        processed = 0
        for cat in categories:
            cat_name = cat['label']
            cat_url = cat['url']
            
            if cat_name in all_products:
                continue # Saltiamo quelle già fatte

            print(f"📂 [{processed}] Elaborazione: {cat_name}")
            try:
                await page.goto(cat_url, wait_until="load", timeout=60000)
                await asyncio.sleep(random.uniform(3, 6))

                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                links = []
                for a in soup.select("a.product-item-link"):
                    href = a['href']
                    if href not in links:
                        links.append(href)
                
                all_products[cat_name] = links
                print(f"   -> Trovati {len(links)} prodotti.")

                # Salvataggio incrementale
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(all_products, f, indent=4, ensure_ascii=False)

                processed += 1
                if processed >= 20: # Limite per singola run
                    print("Limite run raggiunto. Salvo e chiudo.")
                    break

                await asyncio.sleep(random.uniform(5, 10))

            except Exception as e:
                print(f"   ❌ Errore su {cat_name}: {e}")

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(collect_links())
