
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import base64

def decrypt_url(encoded_str):
    try:
        missing_padding = len(encoded_str) % 4
        if missing_padding:
            encoded_str += '=' * (4 - missing_padding)
        step1 = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        if len(step1) > 16:
            clean_b64 = step1[:12] + step1[16:]
            missing_padding = len(clean_b64) % 4
            if missing_padding:
                clean_b64 += '=' * (4 - missing_padding)
            return base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
    except: pass
    return None

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a very common user agent
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        context = await browser.new_context(user_agent=ua)
        page = await context.new_page()
        await stealth_async(page)
        
        url = "https://www.grepool.com/it/piscine-in-acciaio/amazonia-ovale/610-x-375-x-132-cm-3"
        print(f"Visiting {url}")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            html = await page.content()
            if "incapsula" in html.lower() and len(html) < 5000:
                print("Blocked by Incapsula.")
                await page.screenshot(path="blocked.png")
            else:
                print("Successfully loaded page.")
                # Look for JollyGame link
                jolly_encoded = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                    const jolly_link = links.find(a => a.href.includes('storename=jollygame'));
                    if (jolly_link) {
                        const urlParams = new URLSearchParams(jolly_link.href.split('?')[1]);
                        return urlParams.get('store-redirect-url');
                    }
                    return null;
                }''')
                
                if jolly_encoded:
                    decoded = decrypt_url(jolly_encoded)
                    print(f"Found JollyGame link: {decoded}")
                else:
                    # Try to open modal
                    buy_btn = page.locator("button.js-openModal, button:has-text('Acquista'), .product-buy button").first
                    if await buy_btn.is_visible():
                        print("Opening modal...")
                        await buy_btn.click()
                        await page.wait_for_timeout(5000)
                        jolly_encoded_modal = await page.evaluate('''() => {
                            const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                            const jolly_link = links.find(a => a.href.includes('storename=jollygame'));
                            if (jolly_link) {
                                const urlParams = new URLSearchParams(jolly_link.href.split('?')[1]);
                                return urlParams.get('store-redirect-url');
                            }
                            return null;
                        }''')
                        if jolly_encoded_modal:
                            decoded = decrypt_url(jolly_encoded_modal)
                            print(f"Found JollyGame link in modal: {decoded}")
                        else:
                            print("JollyGame link not found in modal.")
                            await page.screenshot(path="modal_open.png")
                    else:
                        print("Buy button not found.")
                        await page.screenshot(path="no_buy_btn.png")
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
