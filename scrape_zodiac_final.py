import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
import csv
import os
import random

class ZodiacScraper:
    def __init__(self):
        self.base_url = "https://www.zodiac-poolcare.it"
        self.visited = set()
        self.products = []
        with open("zodiac_links.json", "r") as f:
            self.queue = json.load(f)
        # Randomize queue to avoid pattern detection
        random.shuffle(self.queue)

    async def scrape(self):
        async with async_playwright() as p:
            # Use a persistent context directory
            user_data_dir = os.path.join(os.getcwd(), "playwright_user_data")
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                slow_mo=random.randint(500, 1500),
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
            page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
            
            # Apply stealth to the context if possible, or to the page
            stealth_cfg = Stealth()
            await stealth_cfg.apply_stealth_async(page)

            print(f"Starting with {len(self.queue)} links using Persistent Context")

            # First visit home and do some "human" things
            try:
                await page.goto(self.base_url, wait_until="load", timeout=60000)
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await page.wait_for_timeout(3000)
                
                # Check for Incapsula
                if await page.locator("#main-iframe").count() > 0:
                    print("Incapsula detected on home. Waiting...")
                    await page.wait_for_timeout(20000)
                
                cookie_button = page.locator("button#onetrust-accept-btn-handler")
                if await cookie_button.is_visible(timeout=5000):
                    await cookie_button.click()
            except:
                pass

            count = 0
            while self.queue and count < 200: # Safety limit
                url = self.queue.pop(0)
                if url in self.visited:
                    continue
                
                self.visited.add(url)
                print(f"[{count}] Processing: {url} (Queue: {len(self.queue)})")

                try:
                    # Random delay
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    await page.goto(url, wait_until="load", timeout=60000)
                    await page.wait_for_timeout(2000)
                    
                    body_class = await page.evaluate("document.body.className")
                    
                    if "page-product" in body_class:
                        await self.scrape_product_page(page, url)
                        count += 1
                    elif "page-category" in body_class:
                        card_links = await page.eval_on_selector_all(".product-card a", "elements => elements.map(e => e.href)")
                        for link in card_links:
                            if self.base_url in link and link not in self.visited:
                                self.queue.append(link)
                    elif not body_class or "Incapsula" in await page.content():
                        print(f"Blocked or empty page for {url}. Waiting longer...")
                        await page.wait_for_timeout(15000)
                        # Retry once
                        await page.reload(wait_until="load")
                        body_class = await page.evaluate("document.body.className")
                        if "page-product" in body_class:
                            await self.scrape_product_page(page, url)
                            count += 1
                                
                except Exception as e:
                    print(f"Error processing {url}: {e}")
                
                # Save progress every 10 products
                if count > 0 and count % 10 == 0:
                    self.save_to_csv()

            await browser_context.close()
            self.save_to_csv()

    async def scrape_product_page(self, page, url):
        print(f"Scraping product: {url}")
        try:
            title = await page.locator(".product-info__variantBlock--title").inner_text()
            subtitle = ""
            try: subtitle = await page.locator(".product-info__variantBlock--category").inner_text()
            except: pass
                
            price = ""
            try:
                price_loc = page.locator(".product-info__variantBlock--price span")
                if await price_loc.count() > 0:
                    price_text = await price_loc.inner_text()
                    price = price_text.replace(".", "").replace(",", ".")
            except: pass
            
            features = []
            try:
                feature_elements = await page.locator(".product-info__variantBlock--list li").all_inner_texts()
                features = [f.strip() for f in feature_elements if f.strip()]
            except: pass
            
            description_html = ""
            try:
                description_html = await page.locator(".productTab__container.description").inner_html()
            except: pass
            
            images = []
            try:
                image_elements = await page.locator(".gallery__carousel img").all()
                for img in image_elements:
                    src = await img.get_attribute("src")
                    if src: images.append(src)
            except: pass
            
            tags = []
            try:
                breadcrumb_elements = await page.locator(".product-breadcrumb__links a span").all_inner_texts()
                tags = [b.strip() for b in breadcrumb_elements if b.strip() and b.strip() != "Prodotti"]
            except: pass

            product_data = {
                "Title": title,
                "Subtitle": subtitle,
                "URL": url,
                "Price": price,
                "Features": "\n".join(features),
                "Description": description_html.strip(),
                "Images": ";".join(images),
                "Tags": ",".join(tags),
                "Category": tags[0] if tags else ""
            }
            self.products.append(product_data)
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

    def save_to_csv(self):
        if not self.products:
            return
        keys = self.products[0].keys()
        with open("zodiac_products_raw.csv", "w", newline="", encoding="utf-8") as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.products)
        print(f"Saved {len(self.products)} products to zodiac_products_raw.csv")

if __name__ == "__main__":
    scraper = ZodiacScraper()
    asyncio.run(scraper.scrape())
