import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function checkTaxonomy() {
  console.log("🔍 Verifica Tassonomia e Collezioni...");
  
  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        vendor
        tags
        collections(first: 5) {
          nodes {
            title
          }
        }
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    products.push(...res.data.products.nodes);
    hasNext = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  let productsWithoutCollection = 0;
  let productsWithoutTags = 0;

  for (const p of products) {
    const categories = p.tags.filter((t: string) => t.startsWith("Categoria:"));
    const collections = p.collections.nodes.map((c: any) => c.title);

    if (categories.length === 0) {
        productsWithoutTags++;
        console.log(`  ❌ [Manca Categoria] ${p.title} (Brand: ${p.vendor}) - Tag attuali: ${p.tags.join(", ") || 'Nessuno'}`);
    }

    if (collections.length === 0) {
        productsWithoutCollection++;
        // console.log(`  ⚠️ [Orfano] ${p.title} - Non appare in nessuna collezione.`);
    }
  }

  console.log("\n📊 REPORT TASSONOMIA:");
  console.log(`📦 Totale Prodotti analizzati: ${products.length}`);
  console.log(`✅ Prodotti con tag Categoria: ${products.length - productsWithoutTags}`);
  console.log(`❌ Prodotti senza tag Categoria: ${productsWithoutTags}`);
  console.log(`⚠️ Prodotti non in nessuna collezione: ${productsWithoutCollection}`);
}

checkTaxonomy().catch(console.error);
