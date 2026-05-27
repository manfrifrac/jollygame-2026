import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function cleanRemainingDuplicates() {
  console.log("🧹 PULIZIA FINALE DUPLICATI SERIE...");

  let hasNextPage = true;
  let cursor = null;
  const map: Record<string, string[]> = {};

  while (hasNextPage) {
    const query = `
    query {
      products(first: 250, query: "vendor:Gre") {
        nodes { id title }
      }
    }
    `;
    const res = await shopifyRequest(query);
    if (!res.data?.products) break;
    
    for (const p of res.data.products.nodes) {
        const t = p.title.trim();
        if (!map[t]) map[t] = [];
        map[t].push(p.id);
    }
    hasNextPage = false; // Gre products should fit in 250 for now
  }

  let deleted = 0;
  for (const title in map) {
      const ids = map[title];
      if (ids.length > 1) {
          console.log(`⚠️  Duplicato rilevato: "${title}" (${ids.length} istanze)`);
          // Teniamo l'ultimo ID creato (solitamente quello corretto con productSet)
          const toKeep = ids[ids.length - 1];
          const toDelete = ids.filter(id => id !== toKeep);
          
          for (const id of toDelete) {
              await shopifyRequest(`mutation { productDelete(input: { id: "${id}" }) { deletedProductId } }`);
              deleted++;
          }
      }
  }

  console.log(`✅ Pulizia completata. Rimossi ${deleted} duplicati residui.`);
}

cleanRemainingDuplicates().catch(console.error);
