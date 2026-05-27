import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
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

async function checkMenuLinkTypes() {
  console.log("🔍 Controllo tipi di link nel Main Menu...");

  const query = `
  {
    menu(handle: "main-menu") {
      items {
        title
        type
        resourceId
        items {
          title
          type
          resourceId
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const menu = res.data?.menu;

  if (!menu) {
    console.log("Menu non trovato.");
    return;
  }

  menu.items.forEach((item: any) => {
    console.log(`\n📂 ${item.title} (Tipo: ${item.type})`);
    item.items.forEach((sub: any) => {
      console.log(`  - ${sub.title} (Tipo: ${sub.type})`);
    });
  });
}

checkMenuLinkTypes().catch(console.error);
