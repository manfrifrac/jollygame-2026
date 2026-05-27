import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkMetafieldDefinition() {
  const query = `
    query {
      metafieldDefinitions(first: 50, ownerType: PRODUCT) {
        nodes {
          namespace
          key
          type {
            name
          }
        }
      }
    }
  `;
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query })
  }).then(r => r.json());

  console.log(JSON.stringify(res.data.metafieldDefinitions.nodes.filter((n: any) => n.namespace === "custom"), null, 2));
}

checkMetafieldDefinition().catch(console.error);
