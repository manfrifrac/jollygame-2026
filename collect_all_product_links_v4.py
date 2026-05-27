import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import random
from bs4 import BeautifulSoup
import json
from rotate_vpn import rotate_mullvad

async def collect_links_with_vpn():
    with open("fluidra_categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    output_file = "fluidra_product_links_map.json"
    all_products = json.load(open(output_file, "r", encoding="utf-8")) if os.path.exists(output_file) else {}

    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
        
        async def launch_browser():
            print("🚀 Lancio browser...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir, 
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                slow_mo=200
            )
            page = context.pages[0]
            await Stealth().apply_stealth_async(page)
            await page.set_viewport_size({"width": 1920, "height": 1080})
            return context, page

        browser_context, page = await launch_browser()

        for cat in categories:
            cat_name = cat['label']
            cat_url = cat['url']
            
            if cat_name in all_products and len(all_products[cat_name]) > 0:
                continue

            print(f"📂 Analisi Categoria: {cat_name}")
            links_in_cat = []
            current_page_url = cat_url
            visited_pages = set()

            while current_page_url and current_page_url not in visited_pages:
                try:
                    visited_pages.add(current_page_url)
                    response = await page.goto(current_page_url, wait_until="load", timeout=90000)
                    
                    if response.status in [403, 429, 504]:
                        print(f"⚠️ Errore {response.status} rilevato. Attivo rotazione VPN...")
                        await browser_context.close()
                        rotate_mullvad()
                        await asyncio.sleep(10)
                        browser_context, page = await launch_browser()
                        visited_pages.remove(current_page_url) # Riprova questa pagina
                        continue

                    await asyncio.sleep(random.uniform(4, 7))
                    content = await page.content()
                    soup = BeautifulSoup(content, 'lxml')
                    
                    new_links = [a['href'] for a in soup.select("a.product-item-link") if a.get('href')]
                    for link in new_links:
                        if link not in links_in_cat:
                            links_in_cat.append(link)
                    
                    print(f"   ✅ Prodotti trovati: {len(links_in_cat)}")
                    
                    next_page = soup.select_one("a.action.next")
                    if next_page and next_page.get('href') and next_page['href'] != current_page_url:
                        current_page_url = next_page['href']
                    else:
                        current_page_url = None
                
                except Exception as e:
                    print(f"   ❌ Errore critico: {e}. Tento rotazione VPN di emergenza...")
                    await browser_context.close()
                    rotate_mullvad()
                    await asyncio.sleep(10)
                    browser_context, page = await launch_browser()
                    continue

            all_products[cat_name] = links_in_cat
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_products, f, indent=4, ensure_ascii=False)
            
            await asyncio.sleep(random.uniform(8, 15))

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(collect_links_with_vpn())
