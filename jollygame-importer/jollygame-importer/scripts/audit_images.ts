import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function checkAllImages() {
  console.log("🔍 Analisi completa del catalogo in corso...");
  
  const query = `
  query ($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage }
      nodes {
        id
        title
        vendor
        mediaCount { count }
        media(first: 10) {
          nodes {
            mediaContentType
            status
          }
        }
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  let totalProducts = 0;
  let productsWithImages = 0;
  let productsMissingImages = 0;
  let failedMediaCount = 0;

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    const page = res.data.products;
    
    for (const product of page.nodes) {
      totalProducts++;
      const images = product.media.nodes.filter((m: any) => m.mediaContentType === 'IMAGE');
      const failed = images.filter((img: any) => img.status === 'FAILED');
      
      if (images.length > 0 && failed.length === 0) {
        productsWithImages++;
      } else {
        productsMissingImages++;
        if (failed.length > 0) failedMediaCount += failed.length;
        console.log(`  ⚠️ [${product.vendor}] ${product.title}: ${images.length} immagini (${failed.length} fallite)`);
      }
    }

    hasNext = page.pageInfo.hasNextPage;
    // cursor = ... (not needed if first 250 covers all)
  }

  console.log("\n📊 RIEPILOGO FINALE:");
  console.log(`✅ Prodotti con immagini OK: ${productsWithImages}`);
  console.log(`❌ Prodotti senza immagini o fallite: ${productsMissingImages}`);
  console.log(`📉 Totale media falliti rilevati: ${failedMediaCount}`);
  console.log(`📦 Totale prodotti analizzati: ${totalProducts}`);
}

checkAllImages().catch(console.error);
