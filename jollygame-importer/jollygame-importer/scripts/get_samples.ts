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

const GET_SAMPLE_PRODUCTS = `
query {
  products(first: 10, sortKey: UPDATED_AT, reverse: true, query: "status:ACTIVE") {
    nodes {
      title
      handle
      status
      vendor
      variants(first: 10) {
        nodes {
          title
          sku
          price
        }
      }
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(GET_SAMPLE_PRODUCTS);
  const products = res.data?.products?.nodes || [];
  
  console.log("--- ESEMPI DI PRODOTTI ONLINE SU SHOPIFY ---");
  
  products.forEach(p => {
      console.log(`\n📦 TITOLO: ${p.title}`);
      console.log(`🏷️ BRAND: ${p.vendor}`);
      console.log(`🔗 LINK AL SITO: https://${SHOP_DOMAIN}/products/${p.handle}`);
      console.log(`⚙️ VARIANTI CARICATE (${p.variants.nodes.length}):`);
      p.variants.nodes.forEach(v => {
          console.log(`   - Opzione: ${v.title} | SKU: ${v.sku || 'N/D'} | Prezzo: €${v.price}`);
      });
  });
}

main().catch(console.error);
