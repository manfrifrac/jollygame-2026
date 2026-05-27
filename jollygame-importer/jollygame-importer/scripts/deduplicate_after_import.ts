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

async function deduplicateProducts() {
  console.log("🧹 Inizio rimozione duplicati massiva...");

  let hasNextPage = true;
  let cursor = null;
  const productsMap: Record<string, string[]> = {}; // title -> [ids]

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
        }
      }
    }
    `;
    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const p of res.data.products.nodes) {
        const title = p.title.toLowerCase().trim();
        if (!productsMap[title]) productsMap[title] = [];
        productsMap[title].push(p.id);
    }
    
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  let deletedCount = 0;
  for (const title in productsMap) {
      const ids = productsMap[title];
      if (ids.length > 1) {
          console.log(`⚠️  Trovati ${ids.length} duplicati per: ${title.substring(0, 50)}...`);
          // Teniamo il primo (solitamente il più vecchio o quello corretto) e cancelliamo gli altri
          const toDelete = ids.slice(1);
          
          for (const id of toDelete) {
              const mutation = `mutation { productDelete(input: { id: "${id}" }) { deletedProductId } }`;
              await shopifyRequest(mutation);
              deletedCount++;
          }
      }
  }

  console.log(`\n✅ Pulizia completata. Rimossi ${deletedCount} prodotti duplicati.`);
}

deduplicateProducts().catch(console.error);
