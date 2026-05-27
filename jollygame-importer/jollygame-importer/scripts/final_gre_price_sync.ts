import { chromium } from "playwright";
import * as fs from "fs";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function syncGrePrices() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    viewport: { width: 1920, height: 1080 }
  });

  // Carica i prodotti mappati (usiamo quelli con URL trovato)
  const products = JSON.parse(fs.readFileSync("gre_mapped_drafts.json", "utf8"));
  // In mancanza di URL da ricerca, usiamo alcuni hardcoded o quelli dell'audit precedente
  const toProcess = products.filter((p: any) => p.gre_url).slice(0, 5);
  
  // Test su uno specifico se la lista è vuota (per dimostrazione)
  if (toProcess.length === 0) {
      toProcess.push({
          id: "gid://shopify/Product/15527814463836",
          title: "Piscina Anthracite Ovale",
          gre_url: "https://www.grepool.com/it/piscine-in-acciaio/anthracite-ovale-paletti-laterali/500-x-300-x-132-cm-5"
      });
  }

  console.log(`🚀 Avvio sincronizzazione prezzi per ${toProcess.length} prodotti Gre...`);

  for (const prod of toProcess) {
    console.log(`\n🔎 Elaborazione: ${prod.title}`);
    const page = await context.newPage();
    
    try {
      await page.goto(prod.gre_url, { waitUntil: "load", timeout: 45000 });
      await page.waitForTimeout(5000);

      // Bypass Cookiebot
      try {
        await page.evaluate(() => {
          const btn = document.querySelector('#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll');
          if (btn) (btn as HTMLElement).click();
        });
        await page.waitForTimeout(2000);
      } catch (e) {}

      // Trova e clicca Acquista
      const buyBtn = page.locator(".js-openModal, .where-to-buy button, button:has-text('Acquista')").first;
      if (await buyBtn.count() > 0) {
        console.log("🖱️ Clic su Acquista...");
        await buyBtn.click({ force: true });
        await page.waitForTimeout(15000); // Attesa Netrivals

        // Estrazione prezzi
        const prices = await page.evaluate(() => {
          const res: string[] = [];
          document.querySelectorAll("*").forEach(el => {
            const t = (el as HTMLElement).innerText;
            if (t && t.includes("€") && t.length < 15 && /\d/.test(t)) {
              res.push(t.trim());
            }
          });
          return [...new Set(res)];
        });

        console.log(`💰 Prezzi trovati: ${JSON.stringify(prices)}`);

        const numeric = prices.map(p => parseFloat(p.replace(/[^\d,.]/g, "").replace(",", "."))).filter(n => n > 100);
        
        if (numeric.length > 0) {
          const minPrice = Math.min(...numeric);
          console.log(`✅ Prezzo minimo individuato: ${minPrice} €`);
          
          // Qui andrebbe la mutation Shopify per aggiornare il prezzo e attivare il prodotto
          // mutation productUpdate(input: { id: prod.id, status: ACTIVE, variants: [{ price: minPrice }] })
        } else {
          console.log("⚠️ Nessun prezzo valido trovato nel widget.");
        }
      } else {
        console.log("❌ Pulsante Acquista non trovato.");
      }
    } catch (err) {
      console.error(`❌ Errore: ${err}`);
    } finally {
      await page.close();
    }
  }

  await browser.close();
}

syncGrePrices().catch(console.error);
