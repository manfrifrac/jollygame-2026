import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function refactorToMultiOptions() {
  const plan = JSON.parse(fs.readFileSync("../../gre_kits_only_plan.json", "utf8"));
  
  console.log("🚀 AVVIO RIFATTORIZZAZIONE MULTI-OPZIONE (Misura + Dotazione)...");

  for (const groupKey in plan) {
      const variants = plan[groupKey];
      const title = `Piscina Gre ${groupKey}`;
      
      console.log(`📦 Refactoring: ${title}`);

      // 1. Estrazione Unica di Misure e Dotazioni
      const measures = new Set();
      const dotazioni = new Set();
      
      const variantInputs = variants.map((v: any) => {
          let m = v.dim;
          let d = "Filtro Sabbia"; // Default

          if (v.sku.includes("GYQ") || v.sku.includes("WQ") || v.sku.includes("QGRE")) d = "Sistema Aqualoon";
          else if (v.sku.includes("ECO")) d = "Filtro Cartuccia (ECO)";
          
          if (v.sku.endsWith("L") || v.sku.includes("LT")) d += " + Faro LED";
          
          // Se per la stessa misura abbiamo più dotazioni identiche, aggiungiamo lo SKU per sicurezza di unicità
          // Ma proviamo prima senza.
          
          measures.add(m);
          dotazioni.add(d);

          return {
              inventoryItem: { sku: v.sku },
              price: v.price,
              optionValues: [
                  { name: m, optionName: "Misura" },
                  { name: d, optionName: "Dotazione" }
              ],
              inventoryPolicy: "CONTINUE"
          };
      });

      // 2. Controllo Duplicati Interni (Shopify non accetta due varianti con le stesse opzioni)
      const seenCombo = new Set();
      const finalVariants = [];
      for (const vi of variantInputs) {
          const combo = `${vi.optionValues[0].name}-${vi.optionValues[1].name}`;
          if (seenCombo.has(combo)) {
              // Se la combo esiste già, aggiungiamo un dettaglio dallo SKU alla dotazione
              vi.optionValues[1].name += ` (${vi.inventoryItem.sku})`;
              dotazioni.add(vi.optionValues[1].name);
          }
          seenCombo.add(`${vi.optionValues[0].name}-${vi.optionValues[1].name}`);
          finalVariants.push(vi);
      }

      // 3. Applicazione tramite productSet
      const res = await shopifyRequest(`
      mutation productSet($input: ProductSetInput!) {
        productSet(input: $input) {
          product { id }
          userErrors { field message }
        }
      }
      `, {
          input: {
              title: title,
              vendor: "Gre",
              productType: "Piscina",
              status: "ACTIVE",
              tags: ["Categoria:Piscine", "Listino:2026", "MultiOption:Active"],
              productOptions: [
                  { name: "Misura", values: Array.from(measures).map(m => ({ name: m })) },
                  { name: "Dotazione", values: Array.from(dotazioni).map(d => ({ name: d })) }
              ],
              variants: finalVariants
          }
      });

      if (res.data?.productSet?.product) {
          console.log(`   ✅ Successo! Ora il cliente ha due menu a tendina.`);
      } else {
          console.error(`   ❌ Errore ${title}:`, JSON.stringify(res.data?.productSet?.userErrors, null, 2));
      }
  }

  console.log("\n✅ RIFATTORIZZAZIONE COMPLETATA. IL NEGOZIO È ORA AL TOP DELLA GAMMA.");
}

refactorToMultiOptions().catch(console.error);
