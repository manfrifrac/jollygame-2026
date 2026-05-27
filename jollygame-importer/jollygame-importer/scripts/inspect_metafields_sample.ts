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
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function inspectProductFields() {
  console.log("🔍 Ispezione campi metafields per un campione di prodotti...");

  const query = `
  query {
    products(first: 10) {
      nodes {
        id
        title
        vendor
        metafields(first: 50) {
          nodes {
            namespace
            key
            value
            type
          }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  products.forEach(product => {
      console.log(`\n📦 Prodotto: ${product.title} (${product.vendor})`);
      const customMetafields = product.metafields.nodes.filter(m => m.namespace === 'custom' || m.namespace === 'global');
      if (customMetafields.length > 0) {
          customMetafields.forEach(m => {
              console.log(`  - ${m.namespace}.${m.key}: ${m.value} (${m.type})`);
          });
      } else {
          console.log("  (Nessun metafield personalizzato trovato)");
      }
  });
}

inspectProductFields().catch(console.error);
