import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

const COUNT_PRODUCTS = `
query {
  productsCount {
    count
  }
}
`;

async function main() {
  const res = await shopifyRequest(COUNT_PRODUCTS);
  console.log("--- CONTEGGIO PRODOTTI ONLINE ---");
  console.log(`Totale prodotti (Master) attualmente su Shopify: ${res.data?.productsCount?.count}`);
}

main().catch(console.error);
