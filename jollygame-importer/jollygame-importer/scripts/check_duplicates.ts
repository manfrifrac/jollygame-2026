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

async function checkDuplicateSkus() {
  console.log("🔍 Controllo duplicati SKU...");

  let hasNextPage = true;
  let cursor = null;
  const skuMap: Record<string, string[]> = {};

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          title
          variants(first: 100) {
            nodes {
              sku
              title
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    const products = res.data.products.nodes;
    
    for (const product of products) {
      for (const variant of product.variants.nodes) {
        if (variant.sku) {
          if (!skuMap[variant.sku]) skuMap[variant.sku] = [];
          skuMap[variant.sku].push(`${product.title} (${variant.title})`);
        }
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const duplicates = Object.entries(skuMap).filter(([sku, products]) => products.length > 1);
  
  if (duplicates.length > 0) {
    console.log(`\n⚠️ Trovati ${duplicates.length} SKU duplicati:`);
    duplicates.forEach(([sku, products]) => {
      console.log(`- SKU: ${sku} è presente in: ${products.join(", ")}`);
    });
  } else {
    console.log("\n✅ Nessun SKU duplicato trovato.");
  }
}

checkDuplicateSkus().catch(console.error);
