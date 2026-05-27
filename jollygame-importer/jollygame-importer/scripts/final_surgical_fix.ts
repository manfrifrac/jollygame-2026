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

async function finalSurgicalFix() {
  const report = JSON.parse(fs.readFileSync("final_product_by_product_report.json", "utf8"));
  const toFix = report.filter((r: any) => r.issues.length > 0);
  
  console.log(`🛠️ Avvio correzione chirurgica di ${toFix.length} prodotti...`);

  for (const item of toFix) {
      // Recuperiamo il prodotto completo per assicurarci di avere i dati aggiornati
      const query = `{
          product(id: "${item.id}") {
              id
              title
              descriptionHtml
              tags
          }
      }`;
      const res = await shopifyRequest(query);
      const p = res.data?.product;
      if (!p) continue;

      let newDesc = p.descriptionHtml || "";
      let newTags = [...p.tags];
      let newTitle = p.title;
      let changed = false;

      // 1. Fix AI Leakage in Description
      if (item.issues.includes("AI_LEAKAGE_DESCRIPTION")) {
          const originalDesc = newDesc;
          newDesc = newDesc.replace(/Ecco una descrizione ottimizzata:?/gi, "")
                           .replace(/Nuovo titolo:.*$/gim, "")
                           .replace(/Rispondi solo con.*$/gim, "")
                           .replace(/Sei un esperto di copywriting.*$/gim, "")
                           .replace(/SKU: \[inserisciSKU\]/gi, "");
          if (newDesc !== originalDesc) {
              console.log(`   ✨ Pulita descrizione per: ${p.title}`);
              changed = true;
          }
      }

      // 2. Fix Missing Subcategory Tag
      if (item.issues.includes("MISSING_SUBCATEGORY_TAG")) {
          const t = p.title.toLowerCase();
          if (t.includes("manico") || t.includes("termometro") || t.includes("erogatore") || t.includes("adesivo") || t.includes("casetta") || t.includes("protezione") || t.includes("barriera") || t.includes("spugne")) {
              newTags.push("Sottocategoria:Altri accessori");
              changed = true;
          } else if (t.includes("bicicletta")) {
              newTags.push("Sottocategoria:Accessori fitness");
              changed = true;
          } else if (t.includes("liner")) {
              newTags.push("Sottocategoria:Liner e riparatori");
              changed = true;
          }
      }

      // 3. Fix Short Title (Zodiac codes)
      if (item.issues.includes("TITLE_TOO_SHORT")) {
          if (p.title === "RE/U" || p.title === "RE/L" || p.title === "RE/I") {
              newTitle = `Scambiatore di calore Zodiac ${p.title}`;
              changed = true;
          } else if (p.title === "PX25") {
              newTitle = "Filtro a cartuccia Zodiac PX25";
              changed = true;
          } else if (p.title === "CS") {
              newTitle = "Filtro a cartuccia Zodiac CS";
              changed = true;
          }
      }

      if (changed) {
          const mutation = `
          mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
              product { id }
              userErrors { message }
            }
          }
          `;
          await shopifyRequest(mutation, {
              input: {
                  id: p.id,
                  title: newTitle,
                  descriptionHtml: newDesc.trim(),
                  tags: Array.from(new Set(newTags))
              }
          });
      }
  }

  console.log("\n✅ Correzione chirurgica completata.");
}

finalSurgicalFix().catch(console.error);
