import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`;

async function shopifyRequest(query: string) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query }),
  });
  return await response.json();
}

async function listDefinitions() {
  const query = `{
    metafieldDefinitions(first: 100, ownerType: PRODUCT) {
      nodes {
        namespace
        key
        name
        type { name }
      }
    }
  }`;
  const res = await shopifyRequest(query);
  console.log(JSON.stringify(res.data?.metafieldDefinitions?.nodes || [], null, 2));
}

listDefinitions().catch(console.error);
