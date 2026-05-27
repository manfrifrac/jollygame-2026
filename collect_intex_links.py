import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import json
from bs4 import BeautifulSoup

async def collect_links():
    with open("intex_categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

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
        
        product_links = {
            "intex_italia": [],
            "intex_ricambi": []
        }

        async def safe_goto(url, retries=3):
            for i in range(retries):
                try:
                    print(f"  Navigating to: {url} (Attempt {i+1})")
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(5000) # Manual wait for JS rendering
                    return True
                except Exception as e:
                    print(f"  Attempt {i+1} failed: {e}")
                    if i == retries - 1:
                        return False
                    await asyncio.sleep(2)

        # --- Intex Italia ---
        print("Collecting links from Intex Italia...")
        for cat in categories["intex_italia"]:
            print(f" Processing category: {cat['label']}")
            if await safe_goto(cat["url"]):
                # Check for subcategories first
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                subcats = soup.select('.list-categories .item a[href], .list-product_categories .item a[href], .list-subcat .item a[href]')
                
                cat_links = [cat["url"]]
                if subcats:
                    for s in subcats:
                        href = s['href']
                        if not href.startswith('http'):
                            href = "https://www.intexitalia.com" + href
                        if href not in cat_links:
                            cat_links.append(href)
                
                # Now visit each subcat to find products
                for url in cat_links:
                    page_num = 1
                    while True:
                        target_url = url if page_num == 1 else f"{url}page/{page_num}/"
                        print(f"  Scanning products: {target_url}")
                        if await safe_goto(target_url):
                            # Scroll to load all products if lazy loaded
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            await page.wait_for_timeout(2000)
                            
                            sub_content = await page.content()
                            sub_soup = BeautifulSoup(sub_content, 'lxml')
                            
                            title = await page.title()
                            if "404" in title or "non trovato" in title.lower():
                                break
                            
                            links = sub_soup.select('a.card.fix, a.woocommerce-LoopProduct-link')
                            if not links:
                                break
                                
                            found_new = False
                            for l in links:
                                href = l['href']
                                if href not in product_links["intex_italia"]:
                                    product_links["intex_italia"].append(href)
                                    found_new = True
                            
                            if not found_new:
                                break
                                
                            page_num += 1
                            if page_num > 20: # fail safe
                                break
                        else:
                            break
            else:
                print(f"  Skipping category {cat['label']} after retries.")

        # --- Intex Ricambi ---
        print("\nCollecting links from Intex Ricambi...")
        for cat in categories["intex_ricambi"]:
            print(f" Processing category: {cat['label']}")
            if await safe_goto(cat["url"]):
                # Check for subcategories
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                subcats = soup.select('.product-categories .cat-item a[href]')
                
                cat_links = [cat["url"]]
                if subcats:
                    for s in subcats:
                        href = s['href']
                        if not href.startswith('http'):
                            href = "https://www.intexricambi.it" + href
                        if href not in cat_links:
                            cat_links.append(href)
                
                for url in cat_links:
                    page_num = 1
                    while True:
                        target_url = url if page_num == 1 else f"{url}page/{page_num}/"
                        print(f"  Scanning products: {target_url}")
                        if await safe_goto(target_url):
                            title = await page.title()
                            if "404" in title or "non trovato" in title.lower():
                                break
                            
                            sub_content = await page.content()
                            sub_soup = BeautifulSoup(sub_content, 'lxml')
                            
                            links = sub_soup.select('a.woocommerce-LoopProduct-link')
                            if not links:
                                break
                                
                            found_new = False
                            for l in links:
                                href = l['href']
                                if href not in product_links["intex_ricambi"]:
                                    product_links["intex_ricambi"].append(href)
                                    found_new = True
                            
                            if not found_new: 
                                break
                                
                            page_num += 1
                            if page_num > 20: 
                                break
                        else:
                            break
            else:
                print(f"  Skipping category {cat['label']} after retries.")

        with open("intex_product_links.json", "w", encoding="utf-8") as f:
            json.dump(product_links, f, indent=4)
        print(f"\nCollected {len(product_links['intex_italia'])} Italia links and {len(product_links['intex_ricambi'])} Ricambi links.")

        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(collect_links())
