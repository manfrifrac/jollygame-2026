import json
import asyncio
from playwright.async_api import async_playwright
import os
import re

async def sku_scraping():
    # Carichiamo i target che non hanno SKU (basandoci su un export o sui risultati precedenti)
    targets_path = r"C:\Users\Riccardo\Desktop\Manfredo\JollyGame\jollygame-importer\jollygame-importer\price_audit_targets.json"
    if not os.path.exists(targets_path): return

    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)

    print(f"🚀 Avvio estrazione SKU per {len(targets)} prodotti...")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for target in targets:
            url = target['url']
            print(f"\n🔍 Ricerca SKU per: {target['title']}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2)

                # Cerchiamo lo SKU con vari pattern comuni
                sku = await page.evaluate("""() => {
                    // 1. Cerca in tabelle tecniche o etichette specifiche
                    const bodyText = document.body.innerText;
                    const patterns = [
                        /Referenza\\s*:\\s*(\\w+)/i,
                        /Codice\\s*:\\s*(\\w+)/i,
                        /Réf\\.\\s*:\\s*(\\w+)/i,
                        /SKU\\s*:\\s*([A-Z0-9_-]+)/i,
                        /Product ID\\s*:\\s*(\\w+)/i
                    ];
                    for (const p of patterns) {
                        const match = bodyText.match(p);
                        if (match) return match[1];
                    }
                    
                    // 2. Cerca in attributi data
                    const el = document.querySelector('[data-sku], [data-product-sku], .sku, .product-reference');
                    if (el) return el.innerText.replace(/Referenza|SKU|Codice|:/gi, '').trim();

                    return null;
                }""")

                if sku:
                    print(f"  ✨ SKU TROVATO: {sku}")
                    target['new_sku'] = str(sku)
                    results.append(target)
                else:
                    # Se non lo troviamo, proviamo a estrarlo dall'URL se sembra un codice
                    url_parts = url.split('/')
                    last_part = url_parts[-1]
                    if re.match(r'^[A-Z0-9-]{5,}$', last_part.upper()):
                        print(f"  📎 SKU suggerito da URL: {last_part}")
                        target['new_sku'] = last_part
                        results.append(target)
                    else:
                        print("  ⚠️ Nessun SKU trovato.")

            except Exception as e:
                print(f"  ❌ Errore: {e}")

        await browser.close()

    with open("sku_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Estrazione SKU completata. Trovati {len(results)} codici.")

if __name__ == "__main__":
    asyncio.run(sku_scraping())
