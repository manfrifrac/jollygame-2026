import json
import asyncio
from playwright.async_api import async_playwright
import os
import re

async def deep_audit_v2():
    targets_path = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\jollygame-importer\jollygame-importer\price_audit_targets.json"
    if not os.path.exists(targets_path): return

    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)

    print(f"🚀 Avvio Audit Totale (Prezzi + SKU) per {len(targets)} prodotti...")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for target in targets:
            url = target['url']
            print(f"\n🔍 Audit: {target['title']} ({url})")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2)

                # 1. Estrazione PREZZO (ld+json o selettori)
                price = await page.evaluate("""() => {
                    const findInJson = (obj) => {
                        if (obj.price) return obj.price;
                        if (obj.offers) {
                            if (Array.isArray(obj.offers)) return obj.offers[0].price;
                            return obj.offers.price;
                        }
                        return null;
                    };
                    const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                    for (const script of scripts) {
                        try {
                            const data = JSON.parse(script.innerText);
                            let p;
                            if (Array.isArray(data)) { for(const item of data) { p = findInJson(item); if(p) return p; } }
                            else { p = findInJson(data); if(p) return p; }
                        } catch (e) {}
                    }
                    const s = ['.price', '.product-price', '.amount', '[itemprop="price"]'].find(sel => document.querySelector(sel));
                    return s ? document.querySelector(s).innerText : null;
                }""")

                # 2. Estrazione SKU (Referenza / Codice)
                sku = await page.evaluate("""() => {
                    // Cerca nel JSON-LD
                    const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                    for (const script of scripts) {
                        try {
                            const data = JSON.parse(script.innerText);
                            const findSku = (obj) => obj.sku || obj.mpn || obj.productID;
                            let s;
                            if (Array.isArray(data)) { for(const item of data) { s = findSku(item); if(s) return s; } }
                            else { s = findSku(data); if(s) return s; }
                        } catch (e) {}
                    }
                    // Cerca nel testo della pagina
                    const bodyText = document.body.innerText;
                    const patterns = [/Réf\\.\\s*:\\s*(\\w+)/i, /Referenza\\s*:\\s*(\\w+)/i, /Codice\\s*:\\s*(\\w+)/i, /SKU\\s*:\\s*(\\w+)/i];
                    for (const p of patterns) {
                        const match = bodyText.match(p);
                        if (match) return match[1];
                    }
                    return null;
                }""")

                if price or sku:
                    print(f"  ✨ TROVATO -> Prezzo: {price} | SKU: {sku}")
                    target['new_price'] = str(price) if price else "0.00"
                    target['new_sku'] = str(sku) if sku else None
                    results.append(target)
                else:
                    print("  ⚠️ Nessun dato utile trovato.")

            except Exception as e:
                print(f"  ❌ Errore: {e}")

        await browser.close()

    with open("audit_results_v2.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Audit completato. Trovati dati per {len(results)} prodotti.")

if __name__ == "__main__":
    asyncio.run(deep_audit_v2())
