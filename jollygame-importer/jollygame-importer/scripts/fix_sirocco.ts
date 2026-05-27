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

async function fixSirocco() {
  console.log("🛠️  Fix specifico per Sirocco²...");

  // 1. Mappa Collezioni
  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const hPId = colMap["pompe di calore"];

  const query = `
    query {
      products(first: 5, query: "title:Sirocco*") {
        nodes { id title }
      }
    }
  `;
  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  for (const product of products) {
      console.log(`🚀 Aggiornamento forzato: ${product.title}`);
      if (hPId) {
          await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, {
              input: { id: product.id, collectionsToJoin: [hPId] }
          });
          console.log("   ✅ Aggiunto a Pompe di Calore.");
      }
  }
}

fixSirocco().catch(console.error);
