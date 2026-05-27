import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function checkTemplateSuffix() {
  console.log("🔍 Controllo Template Suffix di tutti i prodotti attivi...");

  const query = `
  {
    products(first: 250, query: "status:active") {
      nodes {
        id
        title
        templateSuffix
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  const customTemplates = products.filter(p => p.templateSuffix !== null);
  
  if (customTemplates.length === 0) {
      console.log("✅ Tutti i prodotti usano il template Default.");
  } else {
      console.log(`⚠️ ${customTemplates.length} prodotti usano template personalizzati:`);
      console.table(customTemplates.map(p => ({ title: p.title, template: p.templateSuffix })));
  }
}

checkTemplateSuffix().catch(console.error);
