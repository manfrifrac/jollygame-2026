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

const GET_PRODUCT_STATUS = `
query {
  productByHandle(handle: "pompa-filtro-sabbia") {
    id
    title
    status
    onlineStoreUrl
    publishedAt
    resourcePublicationsV2(first: 10) {
      nodes {
        publication {
          id
          name
        }
        isPublished
        publishDate
      }
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(GET_PRODUCT_STATUS);
  console.log(JSON.stringify(res, null, 2));
}

main().catch(console.error);
