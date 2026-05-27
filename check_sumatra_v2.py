
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
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
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        url = "https://www.grepool.com/it/piscine-interrate/sumatra-ovale/500-x-300-x-120-cm-4"
        print(f"Visiting {url}")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # 1. Accept Cookies
            accept_cookies = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll, #CybotCookiebotDialogBodyButtonAccept")
            if await accept_cookies.is_visible():
                print("Accepting cookies...")
                await accept_cookies.click()
                await page.wait_for_timeout(2000)
            
            # 2. Click button to open modal
            buy_btn = page.locator("button.js-openModal, button:has-text('Acquista')").first
            if await buy_btn.is_visible():
                print("Opening modal...")
                await buy_btn.click()
                await page.wait_for_timeout(5000)
            
            # 3. Check for JollyGame link
            data = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                const jolly = links.find(a => a.href.includes('storename=jollygame'));
                return jolly ? jolly.href : null;
            }''')
            
            if data:
                params = dict([p.split('=') for p in data.split('?')[1].split('&') if '=' in p])
                encoded = params.get('store-redirect-url')
                if encoded:
                    decoded = decrypt_url(encoded)
                    print(f"Found JollyGame decoded URL: {decoded}")
            else:
                print("JollyGame link not found.")
                await page.screenshot(path="debug_sumatra_final.png")
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
