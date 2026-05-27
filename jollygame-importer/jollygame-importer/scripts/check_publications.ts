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

const GET_PUBLICATIONS = `
query {
  publications(first: 10) {
    nodes {
      id
      name
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(GET_PUBLICATIONS);
  console.log(JSON.stringify(res.data?.publications?.nodes || [], null, 2));
}

main().catch(console.error);
