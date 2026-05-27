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

async function cleanupFuzzyDuplicates() {
  console.log("🧹 Avvio eliminazione duplicati fuzzy...");

  const report = JSON.parse(fs.readFileSync("fuzzy_duplicates_report.json", "utf-8"));
  let deletedCount = 0;

  for (const group of report) {
    console.log(`\n📦 Gruppo: ${group.normalized_key}`);
    console.log(`  🏆 Tengo: ${group.winner.title} (${group.winner.id})`);
    
    for (const dup of group.duplicates) {
      console.log(`  🗑️ Elimino: ${dup.title} (${dup.id})`);
      
      const mutation = `
        mutation productDelete($input: ProductDeleteInput!) {
          productDelete(input: $input) {
            deletedProductId
            userErrors { field message }
          }
        }
      `;
      
      const res = await shopifyRequest(mutation, { input: { id: dup.id } });
      if (res.data?.productDelete?.deletedProductId) {
        deletedCount++;
        process.stdout.write(".");
      } else {
        console.error(`\n❌ Errore eliminazione ${dup.id}:`, JSON.stringify(res.data?.productDelete?.userErrors));
      }
      await new Promise(r => setTimeout(r, 200));
    }
  }

  console.log(`\n\n✅ Pulizia completata! Totale prodotti eliminati: ${deletedCount}`);
}

cleanupFuzzyDuplicates().catch(console.error);
