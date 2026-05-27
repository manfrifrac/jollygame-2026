
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
            # Pattern discovered: remove 4 chars at index 12
            clean_b64 = step1[:12] + step1[16:]
            missing_padding = len(clean_b64) % 4
            if missing_padding:
                clean_b64 += '=' * (4 - missing_padding)
            return base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
    except: pass
    return None

async def run_alignment():
    # 1. Load Shopify Products
    shopify_file = 'jollygame-importer/jollygame-importer/shopify_gre_products.json'
    if not os.path.exists(shopify_file):
        print("Shopify products file not found.")
        return
    
    with open(shopify_file, 'r', encoding='utf-8') as f:
        shopify_products = json.load(f)
    
    sku_to_product = {}
    for p in shopify_products:
        for v in p['variants']['nodes']:
            if v['sku']:
                sku_to_product[v['sku'].strip().upper()] = p

    # 2. Load Mapping CSV
    csv_path = "mapping_prodotti_jolly_gre_FINALE.csv"
    df = pd.read_csv(csv_path)
    
    results = []
    output_file = "gre_handle_alignment_map.csv"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"🚀 Scanning {len(df)} products for Gre links...")
        
        # We'll focus on products where we don't have a suggested handle yet
        for index, row in df.iterrows():
            sku = str(row['SKU']).strip().upper()
            url = row['Grepool_URL']
            
            if not isinstance(url, str) or not url.startswith("http"):
                continue
                
            print(f"[{index+1}/{len(df)}] SKU: {sku}")
            
            jolly_link = None
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(2000)
                
                # Accept cookies if visible
                accept = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
                if await accept.is_visible():
                    await accept.click()
                    await page.wait_for_timeout(1000)

                # Check for link
                jolly_link = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                    const jolly = links.find(a => a.href.includes('storename=jollygame'));
                    return jolly ? jolly.href : null;
                }''')
                
                if not jolly_link:
                    # Open modal
                    btn = page.locator("button.js-openModal, button:has-text('Acquista')").first
                    if await btn.is_visible():
                        await btn.click()
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
                            old_path = decoded_url.split("jollygame.it")[-1]
                            suggested_handle = old_path.split("/")[-1].replace(".html", "")
                            print(f"  [FOUND] {suggested_handle}")
                except: pass
            
            # If not found on Gre, but we have a SKU, we might want to keep the current one
            # OR we try to find it in other CSVs.
            
            shopify_p = sku_to_product.get(sku)
            current_handle = shopify_p['handle'] if shopify_p else "NOT FOUND"
            product_id = shopify_p['id'] if shopify_p else None

            results.append({
                "SKU": sku,
                "Product_ID": product_id,
                "Gre_URL": url,
                "Old_Jolly_URL": decoded_url,
                "Old_Path": old_path,
                "Suggested_Handle": suggested_handle,
                "Current_Shopify_Handle": current_handle
            })
            
            if (index + 1) % 5 == 0:
                pd.DataFrame(results).to_csv(output_file, index=False)
                
        await browser.close()

    pd.DataFrame(results).to_csv(output_file, index=False)
    print(f"\nMapping complete: {output_file}")

if __name__ == "__main__":
    asyncio.run(run_alignment())
