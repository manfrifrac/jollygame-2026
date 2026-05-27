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

const GET_LATEST_PRODUCTS = `
query {
  products(first: 5, sortKey: UPDATED_AT, reverse: true) {
    nodes {
      id
      title
      handle
      status
      variants(first: 5) {
        nodes {
          sku
          price
        }
      }
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(GET_LATEST_PRODUCTS);
  console.log("--- ULTIMI PRODOTTI AGGIORNATI/CREATI ---");
  console.log(JSON.stringify(res.data?.products?.nodes || [], null, 2));
}

main().catch(console.error);
