import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkSchema() {
  const query = `
    query {
      __type(name: "Mutation") {
        fields {
          name
        }
      }
    }
  `;
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN },
    body: JSON.stringify({ query })
  });
  const data = await res.json();
  const mutationNames = data.data.__type.fields.map(f => f.name);
  console.log("Available Mutations:", mutationNames.filter(name => name.toLowerCase().includes("variant")));
}

checkSchema().catch(console.error);
