import json
import asyncio
from playwright.async_api import async_playwright
import os
import re

async def deep_price_audit():
    targets_path = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\jollygame-importer\jollygame-importer\price_audit_targets.json"
    if not os.path.exists(targets_path): return

    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)

    print(f"🚀 Avvio Audit Prezzi Deep per {len(targets)} prodotti...")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for target in targets:
            url = target['url']
            print(f"\n💰 Controllo: {target['title']} ({url})")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3) # Tempo per caricamento prezzi dinamici

                # 1. Cerca nei metadati SEO (ld+json) - Metodo più affidabile
                price = await page.evaluate("""() => {
                    const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                    for (const script of scripts) {
                        try {
                            const data = JSON.parse(script.innerText);
                            // Cerca in Product o Offer
                            const findPrice = (obj) => {
                                if (obj.price) return obj.price;
                                if (obj.offers) {
                                    if (Array.isArray(obj.offers)) return obj.offers[0].price;
                                    return obj.offers.price;
                                }
                                return null;
                            };
                            let p;
                            if (Array.isArray(data)) {
                                for(const item of data) { p = findPrice(item); if(p) return p; }
                            } else {
                                p = findPrice(data); if(p) return p;
                            }
                        } catch (e) {}
                    }
                    return null;
                }""")

                # 2. Se non trovato, cerca nel testo con selettori comuni
                if not price:
                    price = await page.evaluate("""() => {
                        const selectors = ['.price', '.product-price', '.amount', '[itemprop="price"]', '.current-price'];
                        for (const s of selectors) {
                            const el = document.querySelector(s);
                            if (el) return el.innerText;
                        }
                        return null;
                    }""")

                if price:
                    print(f"  ✨ PREZZO TROVATO: {price}")
                    target['new_price'] = str(price)
                    results.append(target)
                else:
                    print("  ⚠️ Nessun prezzo rilevato sul sito.")

            except Exception as e:
                print(f"  ❌ Errore: {e}")

        await browser.close()

    with open("audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Audit completato. Trovati {len(results)} nuovi prezzi.")

if __name__ == "__main__":
    asyncio.run(deep_price_audit())
