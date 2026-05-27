import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function activateAll() {
  console.log("🚀 Attivazione massiva prodotti...");
  
  const query = `{
    products(first: 250, query: "status:draft") {
      nodes {
        id
        title
      }
    }
  }`;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  if (products.length === 0) {
      console.log("✨ Tutti i prodotti sono già attivi.");
      return;
  }

  for (const p of products) {
    const mutation = `mutation productUpdate($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`;
    await shopifyRequest(mutation, { input: { id: p.id, status: "ACTIVE" } });
    console.log(`✅ Attivato: ${p.title}`);
  }
}

activateAll().catch(console.error);
