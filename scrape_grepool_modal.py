
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import base64
import os

def decrypt_url(encoded_str):
    """Logica di decriptazione Netrivals: Base64 -> Remove 4 chars at index 12 -> Base64."""
    try:
        step1 = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        if len(step1) > 16:
            clean_b64 = step1[:12] + step1[16:]
            final_url = base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
            return final_url
    except: pass
    return None

async def scrape_grepool_links():
    csv_path = "mapping_completo_PER_LAVORO_MANUALE.csv"
    df = pd.read_csv(csv_path)
    
    async with async_playwright() as p:
        # Using channel="chrome" might help bypass some checks
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Add some extra headers
        await page.set_extra_http_headers({
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        })
        
        for index, row in df.iterrows():
            url = row['Grepool_URL']
            sku = row['SKU']
            
            # Skip if already filled
            if pd.notna(row['Redirect_From_DA_INCOLLARE']) and row['Redirect_From_DA_INCOLLARE'] != "":
                continue
            if not isinstance(url, str) or not url.startswith("http"):
                continue
                
            print(f"[{index+1}/{len(df)}] Analizzo SKU: {sku} - URL: {url}")
            try:
                # Use a longer timeout and wait for load state
                await page.goto(url, wait_until='domcontentloaded', timeout=90000)
                await page.wait_for_timeout(5000) # Wait for JS to render
                
                # Check for Incapsula
                html = await page.content()
                if "incapsula" in html.lower() and len(html) < 3000:
                    print("  [WARNING] Bloccato da Incapsula!")
                    # Try to wait a bit more or take a screenshot for debug
                    await page.wait_for_timeout(10000)
                    html = await page.content()
                    if "incapsula" in html.lower() and len(html) < 3000:
                        continue

                # The modal content might be hidden in the DOM
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
                    old_url = decrypt_url(jolly_encoded)
                    if old_url:
                        print(f"  [SUCCESS] Trovato: {old_url}")
                        df.at[index, 'Redirect_From_DA_INCOLLARE'] = old_url.replace("https://jollygame.it", "")
                else:
                    # Try to open the modal
                    buy_btn = page.locator("button.js-openModal, button:has-text('Acquista')").first
                    if await buy_btn.is_visible():
                        await buy_btn.click()
                        await page.wait_for_timeout(3000)
                        
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
                            old_url = decrypt_url(jolly_encoded_modal)
                            if old_url:
                                print(f"  [SUCCESS] Trovato in modale: {old_url}")
                                df.at[index, 'Redirect_From_DA_INCOLLARE'] = old_url.replace("https://jollygame.it", "")
                    else:
                        print("  [!] Link Netrivals non trovato.")
            except Exception as e:
                print(f"  [ERROR] {e}")
            
            # Save progress every 5 entries
            if index % 5 == 0:
                df.to_csv(csv_path, index=False)
                
            # Random delay between requests to look more human
            await asyncio.sleep(2)
                
        df.to_csv(csv_path, index=False)
        print("\nScraping completato e CSV aggiornato.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_grepool_links())
