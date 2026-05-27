import dotenv from "dotenv";
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

async function inspectProduct() {
    const query = `
    query($handle: String!) {
      productByHandle(handle: $handle) {
        title
        metafields(first: 5, namespace: "custom") {
            nodes {
                key
                value
            }
        }
      }
    }
    `;
    const res = await shopifyRequest(query, { handle: "cnx-30-iq" });
    console.log(JSON.stringify(res, null, 2));
}

inspectProduct().catch(console.error);
