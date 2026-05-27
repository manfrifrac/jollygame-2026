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

async function exportFullCatalog() {
  console.log("📥 Esportazione catalogo completo per analisi locale...");

  let hasNextPage = true;
  let cursor = null;
  const allProducts: any[] = [];

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          vendor
          productType
          status
          tags
          descriptionHtml
          mediaCount { count }
          variants(first: 100) {
            nodes {
                id
                sku
                price
            }
          }
          collections(first: 10) {
            nodes {
              title
              handle
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) {
        console.error("Errore nel recupero dati:", res);
        break;
    }

    allProducts.push(...res.data.products.nodes);
    console.log(`   - Scaricati ${allProducts.length} prodotti...`);

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  fs.writeFileSync("master_catalog_dump.json", JSON.stringify(allProducts, null, 2));
  console.log(`\n✅ Catalogo salvato in 'master_catalog_dump.json' (${allProducts.length} prodotti).`);
}

exportFullCatalog().catch(console.error);
