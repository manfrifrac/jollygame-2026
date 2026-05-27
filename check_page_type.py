import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def check_page_type(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth_cfg = Stealth()
        await stealth_cfg.apply_stealth_async(page)
        
        print(f"Checking {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            body_class = await page.evaluate("document.body.className")
            print(f"Body class: {body_class}")
            
            # Check for product specific elements
            has_price = await page.locator(".product-info__variantBlock--price").count() > 0
            has_title = await page.locator(".product-info__variantBlock--title").count() > 0
            
            print(f"Has price: {has_price}, Has title: {has_title}")
            
            # If it's a gamma page, it might have links to products
            product_links = await page.eval_on_selector_all(".product-info__variantBlock--select_list a", "elements => elements.map(e => e.href)")
            print(f"Product variant links: {product_links}")
            
            # Other product cards
            card_links = await page.eval_on_selector_all(".product-card a", "elements => elements.map(e => e.href)")
            print(f"Product card links: {len(card_links)}")
            
        except Exception as e:
            print(f"Error: {e}")
        await browser.close()

if __name__ == "__main__":
    url = "https://www.zodiac-poolcare.it/robot-pulitori/robot-elettrici-per-piscine-residenziali/gamma-alpha-iq-/ra-6900-iq"
    asyncio.run(check_page_type(url))
