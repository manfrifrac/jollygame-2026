import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re

async def test_scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Proviamo una piscina (Amazonia Ovale)
        url = "https://www.grepool.com/it/piscine-in-acciaio/amazonia-ovale/610-x-375-x-132-cm-3"
        print(f"🚀 Navigazione verso: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(5000)
            
            # Screenshot iniziale
            await page.screenshot(path="debug_initial_load.png", full_page=True)

            # Bypass Cookiebot aggressivo
            print("🔍 Tentativo bypass cookie...")
            try:
                await page.evaluate('''() => {
                    const btn = document.querySelector('#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll');
                    if (btn) btn.click();
                }''')
                await page.wait_for_timeout(2000)
            except: pass

            # Cerca il pulsante Acquista
            print("🔍 Ricerca pulsante 'Acquista'...")
            
            # Selettore basato su osservazione siti Gre: spesso hanno un div con id "where-to-buy"
            buy_btn = page.locator(".js-openModal, #where-to-buy button, .where-to-buy button").first
            
            if await buy_btn.count() == 0:
                buy_btn = page.get_by_text(re.compile(r"Acquista|Dove comprare", re.IGNORECASE)).first

            if await buy_btn.count() > 0:
                print(f"🖱️ Clic sul pulsante: {await buy_btn.inner_text()}")
                await buy_btn.click(force=True)
                
                print("⏳ Attesa widget (25s)...")
                await page.wait_for_timeout(25000)
                
                # Screenshot del widget
                await page.screenshot(path="debug_scrape_widget.png", full_page=True)
                
                # Estrazione prezzi ampia con regex corretta
                prices = await page.evaluate('''() => {
                    const res = [];
                    document.querySelectorAll('*').forEach(el => {
                        const t = el.innerText;
                        if (t && t.includes('€') && t.length < 12 && /\\d/.test(t)) {
                            res.push(t.trim());
                        }
                    });
                    return [...new Set(res)];
                }''')
                
                print(f"💰 Prezzi trovati: {prices}")
            else:
                print("❌ Pulsante non trovato. Elenco classi dei bottoni:")
                classes = await page.evaluate("() => Array.from(document.querySelectorAll('button')).map(b => b.className)")
                print(f"Classi bottoni: {list(set(classes))}")
                # Salvataggio HTML per ispezione profonda
                with open("debug_page_failed.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                
        except Exception as e:
            print(f"❌ Errore: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scrape())
