import fs from "fs";
import { parse } from "csv-parse/sync";
import { chromium } from "playwright";

async function scrapeGrePrices() {
  console.log("🔍 Avvio scraping prezzi Grepool...");
  
  const csvPath = "../../estrazione_sku_completa.csv";
  if (!fs.existsSync(csvPath)) {
    console.error("❌ File estrazione_sku_completa.csv non trovato.");
    return;
  }

  const records = parse(fs.readFileSync(csvPath, "utf-8"), { columns: true });
  const results = [];

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  for (const record of records.slice(0, 10)) {
    const sku = record.SKU;
    const url = record.Gre_URL;

    if (!url || !url.includes("grepool.com")) continue;

    console.log(`🌐 Scraping [${sku}]: ${url}`);
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 15000 });
      
      // Tentativo di estrazione prezzo
      // Selettore tipico Gre: .product-price o simile
      const price = await page.evaluate(() => {
        const el = document.querySelector(".price, .current-price, .product-price [itemprop='price']");
        return el ? el.textContent?.trim() : null;
      });

      if (price) {
        console.log(`  💰 Trovato: ${price}`);
        results.push({ sku, url, price });
      } else {
        console.log(`  ⚠️ Prezzo non trovato.`);
      }
    } catch (e) {
      console.error(`  ❌ Errore: ${e.message}`);
    }
    
    // Piccolo delay per non essere bloccati
    await new Promise(r => setTimeout(r, 1000));
    
    // Salvataggio parziale ogni 5 record
    if (results.length % 5 === 0) {
      fs.writeFileSync("gre_scraped_prices.json", JSON.stringify(results, null, 2));
    }
  }

  await browser.close();
  fs.writeFileSync("gre_scraped_prices.json", JSON.stringify(results, null, 2));
  console.log(`\n✅ Scraping completato. Trovati ${results.length} prezzi.`);
}

scrapeGrePrices().catch(console.error);
