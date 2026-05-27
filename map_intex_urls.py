import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
from bs4 import BeautifulSoup

async def scrape_all_intex_categories():
    # Load category URLs from sitemap
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse('intex_cat_sitemap.xml')
        root = tree.getroot()
        cat_urls = [loc.text for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    except:
        print("Sitemap not found, please run the sitemap download first.")
        return

    mapping = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        for url in cat_urls:
            print(f"Scraping category: {url}")
            try:
                await page.goto(url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(3000)
                
                # Scroll to ensure all products load if there's any lazy loading
                for _ in range(3):
                    await page.mouse.wheel(0, 2000)
                    await page.wait_for_timeout(1000)

                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Category name from URL
                cat_name = url.replace("https://www.intexitalia.com/", "").strip("/")
                
                # Find all product links
                # In WooCommerce/Intex, product links usually are in .product a or .item a
                links = soup.select('.product a[href*="/piscine-fuori-terra/"], .product a[href*="/spa-idromassaggio/"], .product a[href*="/airbed/"], .product a[href*="/wetset-playcenter/"], .product a[href*="/sport-e-tempo-libero/"], .product a[href*="/barche/"]')
                # Fallback to a broader search
                if not links:
                    links = [a for a in soup.find_all('a', href=True) if '/prodotto/' in a['href'] or any(x in a['href'] for x in ['/piscine-fuori-terra/', '/spa-idromassaggio/', '/airbed/']) and a['href'].count('/') > 4]

                prod_urls = []
                for a in links:
                    href = a['href'].split('?')[0].rstrip('/')
                    if href.startswith('https://www.intexitalia.com') and href != url.rstrip('/'):
                        prod_urls.append(href)
                
                prod_urls = list(set(prod_urls))
                mapping[cat_name] = prod_urls
                print(f"   -> Found {len(prod_urls)} products.")
                
            except Exception as e:
                print(f"   ❌ Error on {url}: {e}")

        await browser.close()

    with open("intex_url_category_map.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=4)
    
    print("\n✅ Mappatura URL-Categoria completata.")

if __name__ == "__main__":
    asyncio.run(scrape_all_intex_categories())
