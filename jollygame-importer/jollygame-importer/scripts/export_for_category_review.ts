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

async function exportProductCategories() {
  console.log("🔍 Esportazione dati per revisione categorie...");

  let hasNextPage = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
          handle
          collections(first: 10) {
            nodes {
              title
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    products.push(...res.data.products.nodes);
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const mapping = products.map(p => ({
    id: p.id,
    title: p.title,
    vendor: p.vendor,
    current_collections: p.collections.nodes.map((c: any) => c.title).join(", "),
    suggested_category: "" // Da riempire via script
  }));

  fs.writeFileSync("product_category_review.json", JSON.stringify(mapping, null, 2));
  console.log(`✅ Esportati ${mapping.length} prodotti in 'product_category_review.json'`);
}

exportProductCategories().catch(console.error);
