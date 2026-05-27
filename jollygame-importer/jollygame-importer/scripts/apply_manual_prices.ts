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

const GET_PRODUCT_VARIANTS = `
query getProductVariants($id: ID!) {
  product(id: $id) {
    variants(first: 10) {
      nodes { id title }
    }
  }
}
`;

async function applyFoundPrices() {
  const foundPrices: Record<string, string> = {
    "KPCOR2814T": "4225.00",
    "KPCOR28T": "5095.00",
    "SWGA40": "990.00",
    "TRCP96": "459.00",
    "PP152": "299.00",
    "40817": "19.90",
    "90003": "22.99",
    "KITPROV508GY": "2499.00",
    "UVC25": "243.99",
    "CFAQ35": "79.90",
    "7015C001": "28.90",
    "76026": "99.90",
    "76048": "32.90",
    "76050": "19.90",
    "76081": "29.00",
    "40080": "8.00",
    "40553": "18.50"
  };

  console.log("💰 Applicazione prezzi trovati online...");

  // Recuperiamo i prodotti attuali per mappare gli SKU agli ID Shopify
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
      if (variant.sku && foundPrices[variant.sku]) {
        variantUpdates.push({
          id: variant.id,
          price: foundPrices[variant.sku]
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

applyFoundPrices().catch(console.error);
