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

const GET_COLLECTIONS = `
query {
  collections(first: 20) {
    nodes {
      id
      title
      handle
    }
  }
}
`;

const COLLECTION_ADD = `
mutation collectionAddProducts($id: ID!, $productIds: [ID!]!) {
  collectionAddProducts(id: $id, productIds: $productIds) {
    collection { id }
    userErrors { field message }
  }
}
`;

async function main() {
  // 1. Get Collections
  const collRes = await shopifyRequest(GET_COLLECTIONS);
  const collections = collRes.data.collections.nodes;
  
  // 2. Get Products
  const prodRes = await shopifyRequest(`
    query {
      products(first: 250, query: "status:ACTIVE") {
        nodes { id title tags }
      }
    }
  `);
  
  const products = prodRes.data.products.nodes;
  
  console.log(`🚀 Assegnazione automatica a collezioni...`);
  
  for (const p of products) {
    const tags = p.tags.map((t: string) => t.toLowerCase());
    
    // Mapping: cerchiamo collezioni che corrispondono ai tag
    for (const c of collections) {
      if (
        (tags.includes('categoria:piscine') && c.title.toLowerCase().includes('piscine')) ||
        (tags.includes('categoria:filtraggio') && c.title.toLowerCase().includes('filtraggio')) ||
        (tags.includes('categoria:coperture') && c.title.toLowerCase().includes('coperture')) ||
        (tags.includes('categoria:accessori') && c.title.toLowerCase().includes('accessori'))
      ) {
        console.log(`  ➕ Aggiungo ${p.title} a ${c.title}`);
        await shopifyRequest(COLLECTION_ADD, { id: c.id, productIds: [p.id] });
      }
    }
  }
  console.log("✅ Collezioni aggiornate!");
}

main().catch(console.error);
