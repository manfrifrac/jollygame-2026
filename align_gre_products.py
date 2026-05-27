
import asyncio
import pandas as pd
import json
import base64
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Configuration
SHOPIFY_API_URL = "https://jollygamepiscine.myshopify.com/admin/api/2024-10/graphql.json"
SHOPIFY_ACCESS_TOKEN = "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"

def decrypt_url(encoded_str):
    try:
        # Step 1: Base64 decode
        missing_padding = len(encoded_str) % 4
        if missing_padding:
            encoded_str += '=' * (4 - missing_padding)
        step1 = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        
        # Step 2: Remove 4 noise chars at index 12
        if len(step1) > 16:
            clean_b64 = step1[:12] + step1[16:]
            # Step 3: Base64 decode again
            # We use a trick to fix padding for the second decode
            missing_padding = len(clean_b64) % 4
            if missing_padding:
                clean_b64 += '=' * (4 - missing_padding)
            
            # Python's b64decode can be picky about length, we try to fix it
            # if 157 % 4 == 1, we might need to remove the last char if it's noise or add 3
            # But actually, the noise is at index 12.
            try:
                return base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
            except:
                # Fallback: try to decode parts
                return "DECODE_ERROR"
    except: pass
    return None

async def run_alignment():
    # 1. Load Shopify Products
    shopify_file = 'jollygame-importer/jollygame-importer/shopify_gre_products.json'
    if not os.path.exists(shopify_file):
        print("Shopify products file not found. Please run fetch_shopify_gre.js first.")
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
    if not os.path.exists(csv_path):
        print("CSV Mapping not found.")
        return
    df = pd.read_csv(csv_path)
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"🚀 Starting alignment for {len(df)} products...")
        
        for index, row in df.iterrows():
            sku = str(row['SKU']).strip().upper()
            url = row['Grepool_URL']
            
            if not isinstance(url, str) or not url.startswith("http"):
                continue
                
            print(f"[{index+1}/{len(df)}] Analyzing SKU: {sku} - URL: {url}")
            
            jolly_link = None
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Check for JollyGame link in DOM
                jolly_link = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                    const jolly = links.find(a => a.href.includes('storename=jollygame'));
                    return jolly ? jolly.href : null;
                }''')
                
                if not jolly_link:
                    # Try to open modal
                    buy_btn = page.locator("button.js-openModal, button:has-text('Acquista')").first
                    if await buy_btn.is_visible():
                        await buy_btn.click()
                        await page.wait_for_timeout(3000)
                        jolly_link = await page.evaluate('''() => {
                            const links = Array.from(document.querySelectorAll("a[href*='netrivals.com']"));
                            const jolly = links.find(a => a.href.includes('storename=jollygame'));
                            return jolly ? jolly.href : null;
                        }''')
            except Exception as e:
                print(f"  Error: {e}")
            
            decoded_url = None
            suggested_handle = None
            if jolly_link:
                try:
                    params = dict([p.split('=') for p in jolly_link.split('?')[1].split('&') if '=' in p])
                    encoded = params.get('store-redirect-url')
                    if encoded:
                        decoded_url = decrypt_url(encoded)
                        if decoded_url and "jollygame.it" in decoded_url:
                            # Extract slug from URL
                            # https://www.jollygame.it/category/slug.html -> slug
                            path = decoded_url.split("jollygame.it/")[-1]
                            slug = path.split("/")[-1].replace(".html", "")
                            suggested_handle = slug
                            print(f"  [SUCCESS] Decoded URL: {decoded_url} -> Slug: {slug}")
                except:
                    print("  [ERROR] Failed to parse/decode Netrivals link.")
            else:
                print("  [INFO] JollyGame link not found.")

            # Match with Shopify
            shopify_p = sku_to_product.get(sku)
            current_handle = shopify_p['handle'] if shopify_p else "NOT FOUND"
            
            status = "Match"
            if suggested_handle and suggested_handle != current_handle:
                status = "Update Needed"
            elif not suggested_handle:
                status = "Not on Gre"
            
            results.append({
                "SKU": sku,
                "Grepool_URL": url,
                "Gre_Popup_URL": decoded_url,
                "Suggested_Handle": suggested_handle,
                "Shopify_Current_Handle": current_handle,
                "Status": status
            })
            
            # Save progress every 10 products
            if (index + 1) % 10 == 0:
                pd.DataFrame(results).to_csv("gre_alignment_progress.csv", index=False)
                
        await browser.close()

    # Save final results
    res_df = pd.DataFrame(results)
    res_df.to_csv("gre_alignment_final_report.csv", index=False)
    print("\n✅ Final report saved to gre_alignment_final_report.csv")

if __name__ == "__main__":
    asyncio.run(run_alignment())
