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

async function applyBatch3Prices() {
  const batch3Prices: Record<string, string> = {
    "76028": "65.00",
    "40802": "17.90",
    "AR82": "24.00",
    "UFG20": "5.50",
    "76054L": "55.90",
    "40582": "4.00",
    "7015R002": "155.00",
    "7015C002": "34.00",
    "787247": "420.00",
    "126674": "269.00"
  };

  console.log("💰 Applicazione Batch 3 di prezzi trovati online...");

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
      if (variant.sku && batch3Prices[variant.sku]) {
        variantUpdates.push({
          id: variant.id,
          price: batch3Prices[variant.sku]
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

applyBatch3Prices().catch(console.error);
