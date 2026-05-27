
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
        
        url = "https://www.grepool.com/it/piscine-in-acciaio/amazonia-ovale/610-x-375-x-132-cm-3"
        print(f"Visiting {url}")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Check for buy button / modal
            buy_btn = page.locator("button.js-openModal, button:has-text('Acquista')").first
            if await buy_btn.is_visible():
                print("Opening modal...")
                await buy_btn.click()
                await page.wait_for_timeout(5000)
            
            links_data = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll("a[href*='netrivals.com']"))
                    .map(a => ({ href: a.href, text: a.innerText }));
            }''')
            
            print(f"Found {len(links_data)} netrivals links.")
            for ld in links_data:
                print(f"Link: {ld['href']} | Text: {ld['text']}")
                if 'jollygame' in ld['href'].lower():
                    params = dict([p.split('=') for p in ld['href'].split('?')[1].split('&') if '=' in p])
                    encoded = params.get('store-redirect-url')
                    if encoded:
                        print(f"Decoded JollyGame: {decrypt_url(encoded)}")
            
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
