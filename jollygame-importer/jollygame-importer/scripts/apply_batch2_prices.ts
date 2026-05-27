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

const PRODUCT_VARIANTS_BULK_UPDATE = `
mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants { id price }
    userErrors { field message }
  }
}
`;

async function applyBatch2Prices() {
  const batch2Prices: Record<string, string> = {
    "KITPR358GY": "1369.00",
    "KIT500GYQGRE": "1549.00",
    "KIT300GYQGRE": "909.00",
    "MG320NP": "205.00",
    "HPM40": "715.00",
    "AR2000": "143.00",
    "CVKPCO41": "148.00",
    "7015C004": "68.00",
    "40001": "42.00",
    "40010": "19.90"
  };

  console.log("💰 Applicazione Batch 2 di prezzi trovati online...");

  const query = `
    query {
      products(first: 250) {
        nodes {
          id
          variants(first: 50) {
            nodes {
              id
              sku
            }
          }
        }
      }
    }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  for (const product of products) {
    const variantUpdates = [];
    for (const variant of product.variants.nodes) {
      if (variant.sku && batch2Prices[variant.sku]) {
        variantUpdates.push({
          id: variant.id,
          price: batch2Prices[variant.sku]
        });
      }
    }

    if (variantUpdates.length > 0) {
      console.log(`🏷️ Aggiornamento prezzi per prodotto ${product.id}...`);
      const updateRes = await shopifyRequest(PRODUCT_VARIANTS_BULK_UPDATE, {
        productId: product.id,
        variants: variantUpdates
      });
      if (updateRes.data?.productVariantsBulkUpdate?.productVariants) {
        console.log(`  ✅ ${variantUpdates.length} varianti aggiornate.`);
      } else {
        console.error(`  ❌ Errore:`, JSON.stringify(updateRes.data?.productVariantsBulkUpdate?.userErrors));
      }
    }
  }
}

applyBatch2Prices().catch(console.error);
