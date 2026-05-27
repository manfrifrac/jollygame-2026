import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from bs4 import BeautifulSoup

async def analyze_fluidra_category(url):
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
        
        print(f"Navigating to: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=90000)
            await page.wait_for_timeout(5000)
            
            # More aggressive scrolling
            for i in range(10):
                await page.mouse.wheel(0, 2000)
                await page.wait_for_timeout(1000)
            
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # Find all links and filter them
            all_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)
                if "/it_it/" in href and href.endswith(".html"):
                    # Filter out obvious category/system links
                    if not any(x in href for x in ["/catalog/category/", "/customer/", "/checkout/", "contact", "about-us", "privacy", "cookies", "terms"]):
                        all_links.append({"text": text, "url": href})
            
            # Unique links
            unique_links = {l['url']: l for l in all_links}.values()
            print(f"Found {len(unique_links)} potential product links.")
            
            for i, l in enumerate(list(unique_links)[:20]):
                print(f"{i+1}. {l['text']} -> {l['url']}")
            
            # Try to identify product container
            # Look for common Magento containers if it's Magento
            # .product-item, .item.product, etc.
            
            containers = soup.select(".product-item, .item.product, .product-container, .product-card")
            print(f"Found {len(containers)} standard product containers.")
            
            await page.screenshot(path="analyze_fluidra_category.png", full_page=True)
            with open("analyze_fluidra_category.html", "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser_context.close()

if __name__ == "__main__":
    # Pompe autoadescanti
    target = "https://pro.fluidra.com/it_it/catalog/category/view/s/pompe-autoadescanti/id/50185/"
    asyncio.run(analyze_fluidra_category(target))
