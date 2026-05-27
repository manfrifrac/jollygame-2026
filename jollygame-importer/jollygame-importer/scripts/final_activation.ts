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

async function activateAll() {
  console.log("🚀 Attivazione massiva di tutti i prodotti...");

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
    query getDrafts($cursor: String) {
      products(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { id status }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    const products = res.data.products.nodes;

    for (const product of products) {
      if (product.status !== "ACTIVE") {
        const mutation = `
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id status }
            userErrors { field message }
          }
        }
        `;
        const updateRes = await shopifyRequest(mutation, {
          input: { id: product.id, status: "ACTIVE" }
        });
        if (updateRes.data?.productUpdate?.product) {
          updatedCount++;
          process.stdout.write(".");
        }
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n\n✅ Attivazione completata! ${updatedCount} prodotti portati in stato ACTIVE.`);
}

activateAll().catch(console.error);
