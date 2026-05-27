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

async function finalLinerFix() {
  console.log("🛠️  Spostamento Liner (Query Corretta V3)...");

  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const linerId = colMap["liner e riparatori"];
  const badId = colMap["piscine fuori terra"];

  const query = `
    query {
      products(first: 250) {
        nodes {
          id title collections(first: 20) { nodes { id title } }
        }
      }
    }
  `;
  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  for (const product of products) {
      if (product.title.toLowerCase().includes("liner")) {
          const currentIds = product.collections.nodes.map((c: any) => c.id);
          const join = [];
          const leave = [];

          if (linerId && !currentIds.includes(linerId)) join.push(linerId);
          if (badId && currentIds.includes(badId)) leave.push(badId);

          if (join.length > 0 || leave.length > 0) {
              console.log(`✨ Fix: ${product.title}`);
              await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, {
                  input: { id: product.id, collectionsToJoin: join, collectionsToLeave: leave }
              });
          }
      }
  }
  console.log("✅ Finito.");
}

finalLinerFix().catch(console.error);
