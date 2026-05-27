
import asyncio
import pandas as pd
import json
import base64
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

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

async def run_scraper():
    csv_path = "mapping_prodotti_jolly_gre_FINALE.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
    
    df = pd.read_csv(csv_path)
    results = []
    
    output_file = "gre_alignment_results.csv"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"🚀 Starting scraper for {len(df)} products...")
        
        for index, row in df.iterrows():
            sku = str(row['SKU']).strip().upper()
            url = row['Grepool_URL']
            
            if not isinstance(url, str) or not url.startswith("http"):
                continue
                
            print(f"[{index+1}/{len(df)}] SKU: {sku} - URL: {url}")
            
            jolly_link = None
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=45000)
                await page.wait_for_timeout(2000)
                
                # 1. Accept Cookies (mandatory for modal to work sometimes)
                accept_cookies = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll, #CybotCookiebotDialogBodyButtonAccept").first
                if await accept_cookies.is_visible():
                    await accept_cookies.click()
                    await page.wait_for_timeout(1000)
                
                # 2. Check if JollyGame link is already in DOM
                jolly_link = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                    const jolly = links.find(a => a.href.includes('storename=jollygame'));
                    return jolly ? jolly.href : null;
                }''')
                
                if not jolly_link:
                    # 3. Try to open modal
                    buy_btn = page.locator("button.js-openModal, button:has-text('Acquista'), .product-buy button").first
                    if await buy_btn.is_visible():
                        # Use click with force=True if intercepted
                        try:
                            await buy_btn.click(timeout=5000)
                        except:
                            await page.evaluate('(sel) => document.querySelector(sel).click()', "button.js-openModal")
                            
                        await page.wait_for_timeout(3000)
                        
                        jolly_link = await page.evaluate('''() => {
                            const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                            const jolly = links.find(a => a.href.includes('storename=jollygame'));
                            return jolly ? jolly.href : null;
                        }''')
            except Exception as e:
                print(f"  [ERROR] {e}")
            
            decoded_url = None
            suggested_handle = None
            old_path = None
            if jolly_link:
                try:
                    params = dict([p.split('=') for p in jolly_link.split('?')[1].split('&') if '=' in p])
                    encoded = params.get('store-redirect-url')
                    if encoded:
                        decoded_url = decrypt_url(encoded)
                        if decoded_url and "jollygame.it" in decoded_url:
                            # Extract path and handle
                            # https://www.jollygame.it/category/handle.html
                            old_path = decoded_url.split("jollygame.it")[-1]
                            suggested_handle = old_path.split("/")[-1].replace(".html", "")
                            print(f"  [SUCCESS] Found: {suggested_handle}")
                except: pass
            else:
                print("  [INFO] JollyGame link not found.")

            results.append({
                "SKU": sku,
                "Grepool_URL": url,
                "JollyGame_Old_URL": decoded_url,
                "Old_Path": old_path,
                "Suggested_Handle": suggested_handle
            })
            
            # Intermediate save
            if (index + 1) % 5 == 0:
                pd.DataFrame(results).to_csv(output_file, index=False)
                
        await browser.close()

    final_df = pd.DataFrame(results)
    final_df.to_csv(output_file, index=False)
    print(f"\nScraping complete. Results saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(run_scraper())
