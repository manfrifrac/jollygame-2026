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

async function exportAllVariants() {
  console.log("📥 Esportazione di tutte le varianti...");

  let hasNextPage = true;
  let cursor = null;
  const allVariants: any[] = [];

  while (hasNextPage) {
    const query = `
    query getVariants($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          variants(first: 100) {
            nodes {
              id
              title
              sku
              price
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        for (const variant of product.variants.nodes) {
            allVariants.push({
                product_id: product.id,
                product_title: product.title,
                variant_id: variant.id,
                variant_title: variant.title,
                sku: variant.sku,
                current_price: variant.price
            });
        }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  fs.writeFileSync("all_shopify_variants.json", JSON.stringify(allVariants, null, 2));
  console.log(`✅ Esportate ${allVariants.length} varianti.`);
}

exportAllVariants().catch(console.error);
