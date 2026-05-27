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

async function cleanupDuplicates() {
  console.log("🧹 Avvio pulizia duplicati fantasma...");

  let hasNextPage = true;
  let cursor = null;
  const productGroups: Record<string, any[]> = {};

  // 1. Raccogliamo tutti i prodotti con i loro metadati critici
  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          mediaCount { count }
          status
          variants(first: 1) {
            nodes {
              price
              sku
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const key = product.title.toLowerCase().trim();
        if (!productGroups[key]) productGroups[key] = [];
        productGroups[key].push(product);
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const toDelete: string[] = [];
  const kept: string[] = [];

  // 2. Analizziamo i gruppi e decidiamo chi tenere
  for (const [title, products] of Object.entries(productGroups)) {
    if (products.length > 1) {
      // Ordiniamo per qualità: prezzo > 0 prima, poi più immagini, poi ACTIVE prima di DRAFT
      const sorted = products.sort((a, b) => {
        const priceA = parseFloat(a.variants.nodes[0]?.price || "0");
        const priceB = parseFloat(b.variants.nodes[0]?.price || "0");
        
        if (priceA !== priceB) return priceB - priceA; // Prezzo più alto vince
        if (a.mediaCount.count !== b.mediaCount.count) return b.mediaCount.count - a.mediaCount.count;
        if (a.status !== b.status) return a.status === "ACTIVE" ? -1 : 1;
        return 0;
      });

      const winner = sorted[0];
      const losers = sorted.slice(1);

      console.log(`\n📦 Gruppo: "${title}"`);
      console.log(`  🏆 TENGO: ${winner.id} (Prezzo: ${winner.variants.nodes[0]?.price}, Immagini: ${winner.mediaCount.count})`);
      
      for (const loser of losers) {
          console.log(`  🗑️ ELIMINO: ${loser.id} (Prezzo: ${loser.variants.nodes[0]?.price}, Immagini: ${loser.mediaCount.count})`);
          toDelete.push(loser.id);
      }
      kept.push(winner.id);
    }
  }

  console.log(`\n⚠️ Totale prodotti da eliminare: ${toDelete.length}`);

  // 3. Esecuzione eliminazione (con cautela e rate limiting)
  if (toDelete.length > 0) {
    console.log("🚀 Esecuzione eliminazione in corso...");
    for (const id of toDelete) {
        const mutation = `
        mutation productDelete($input: ProductDeleteInput!) {
          productDelete(input: $input) {
            deletedProductId
            userErrors { field message }
          }
        }
        `;
        const delRes = await shopifyRequest(mutation, { input: { id } });
        if (delRes.data?.productDelete?.deletedProductId) {
            process.stdout.write(".");
        } else {
            console.error(`\n❌ Errore eliminazione ${id}:`, JSON.stringify(delRes.data?.productDelete?.userErrors));
        }
        await new Promise(r => setTimeout(r, 200)); // Rispetto del rate limit
    }
    console.log("\n✅ Pulizia completata!");
  } else {
    console.log("✅ Nessun duplicato trovato da eliminare.");
  }
}

cleanupDuplicates().catch(console.error);
