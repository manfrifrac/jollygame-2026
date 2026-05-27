import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function findProducts(queryStr: string) {
  const query = `
  query($query: String!) {
    products(first: 10, query: $query) {
      nodes {
        id
        title
        variants(first: 5) {
          nodes {
            id
            price
            sku
          }
        }
      }
    }
  }
  `;

  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables: { query: queryStr } }),
  }).then(r => r.json());

  console.log(JSON.stringify(res.data.products.nodes, null, 2));
}

findProducts("RA 6300").catch(console.error);
