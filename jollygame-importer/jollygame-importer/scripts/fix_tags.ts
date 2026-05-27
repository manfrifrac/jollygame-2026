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

const PRODUCT_TAGS_UPDATE = `
mutation productUpdate($input: ProductInput!) {
  productUpdate(input: $input) {
    product { id tags }
    userErrors { field message }
  }
}
`;

async function main() {
  const prodRes = await shopifyRequest(`
    query {
      products(first: 250, query: "status:ACTIVE") {
        nodes { id tags }
      }
    }
  `);
  
  const products = prodRes.data.products.nodes;
  
  console.log(`🚀 Pulizia chirurgica tag...`);
  
  for (const p of products) {
    let tags = p.tags.map((t: string) => t.toLowerCase());
    
    // Logica di bonifica: se ha un tag tecnico, rimuovi 'categoria:piscine'
    const hasTechnicalTag = tags.includes('categoria:filtraggio') || 
                            tags.includes('categoria:accessori') || 
                            tags.includes('categoria:coperture');
                            
    if (hasTechnicalTag && tags.includes('categoria:piscine')) {
        console.log(`  ✂️ Pulizia: ${p.id}`);
        const newTags = p.tags.filter((t: string) => t.toLowerCase() !== 'categoria:piscine');
        
        await shopifyRequest(PRODUCT_TAGS_UPDATE, {
            input: { id: p.id, tags: newTags }
        });
    }
  }
  console.log("✅ Tag puliti!");
}

main().catch(console.error);
