import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function inspectProduct(title: string) {
  const query = `
  query($query: String!) {
    products(first: 1, query: $query) {
      nodes {
        id
        title
        mediaCount { count }
        media(first: 10) {
          nodes {
            id
            mediaContentType
            status
          }
        }
      }
    }
  }
  `;

  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables: { query: `title:'${title}'` } }),
  }).then(r => r.json());

  console.log(JSON.stringify(res, null, 2));
}

inspectProduct("SWY 3520").catch(console.error);
