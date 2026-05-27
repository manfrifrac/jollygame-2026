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

async function fixVariantTitlesDefinitive() {
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  const pools = data.filter((p: any) => p.title.includes("Piscina Gre"));
  
  console.log(`🛠️ Avvio rinomina varianti DEFINITIVA (con SKU per unicità)...`);

  for (const p of pools) {
      console.log(`📦 Prodotto: ${p.title}`);
      
      const variantUpdates: any[] = [];
      const seenNames = new Set();
      
      for (const v of p.variants.nodes) {
          const sku = (v.sku || "").toUpperCase();
          let baseName = "";
          
          // 1. Estrazione Misura
          if (sku.includes("730")) baseName = "730x375";
          else if (sku.includes("610")) baseName = "610x375";
          else if (sku.includes("500")) baseName = "500x300";
          else if (sku.includes("550")) baseName = "Ø 550";
          else if (sku.includes("460")) baseName = "Ø 460";
          else if (sku.includes("350")) baseName = "Ø 350";
          else if (sku.includes("300")) baseName = "Ø 300";
          else if (sku.includes("240")) baseName = "Ø 240";
          else baseName = "Misura Standard";

          // 2. Dettaglio Filtro/Sistema
          let details: string[] = [];
          if (sku.includes("88") || sku.includes("OMEGA")) details.push("Omega");
          if (sku.includes("GYQ") || sku.includes("WQ") || sku.includes("QGRE")) details.push("Aqualoon");
          else if (sku.includes("ECO")) details.push("Cartuccia");
          else if (sku.startsWith("KIT") || sku.includes("SABBIA")) details.push("Sabbia");

          if (sku.endsWith("L") || sku.includes("LT")) details.push("Faro LED");

          let finalName = baseName;
          if (details.length > 0) finalName += " - " + details.join(" / ");

          // 3. Garanzia Unicità (Se il nome esiste già, aggiungi lo SKU)
          if (seenNames.has(finalName)) {
              finalName += ` (${sku})`;
          }
          seenNames.add(finalName);

          variantUpdates.push({
              id: v.id,
              optionValues: [{ name: finalName, optionName: "Misura e Dotazione" }]
          });
      }

      const res = await shopifyRequest(`
      mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
        productVariantsBulkUpdate(productId: $productId, variants: $variants) {
          userErrors { message }
        }
      }
      `, {
          productId: p.id,
          variants: variantUpdates
      });

      if (!res.data?.productVariantsBulkUpdate?.userErrors?.length) {
          console.log(`   ✅ Varianti rinominate.`);
      } else {
          console.error(`   ❌ Errore rinomina:`, res.data.productVariantsBulkUpdate.userErrors);
      }
  }

  console.log("\n✅ TUTTI I NOMI VARIANTI SONO ORA UNIVOCI E PROFESSIONALI.");
}

fixVariantTitlesDefinitive().catch(console.error);
