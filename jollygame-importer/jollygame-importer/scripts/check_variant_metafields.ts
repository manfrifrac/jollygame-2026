import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkVariantMetafields() {
  const query = `
    query {
      metafieldDefinitions(first: 50, ownerType: PRODUCTVARIANT) {
        nodes {
          namespace
          key
          name
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

  console.log("📊 Metafield definiti per le VARIANTI:");
  if (res.data?.metafieldDefinitions?.nodes) {
      console.log(JSON.stringify(res.data.metafieldDefinitions.nodes, null, 2));
  } else {
      console.log("Nessun metafield trovato per le varianti.");
  }
}

checkVariantMetafields().catch(console.error);
