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

async function getMenuDetails() {
  console.log("🔍 Recupero Dettagli Menu tramite Lista Menus...");

  const query = `
  {
    menus(first: 5) {
      nodes {
        title
        handle
        items {
          title
          url
          items {
            title
            url
            items {
              title
              url
            }
          }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const menus = res.data?.menus?.nodes;

  if (!menus) {
    console.log("Nessun menu trovato.");
    return;
  }

  menus.forEach((menu: any) => {
    console.log(`\n📂 MENU: ${menu.title} (${menu.handle})`);
    
    function printItems(items: any[], indent = "") {
      items.forEach(item => {
        console.log(`${indent}- ${item.title} (${item.url})`);
        if (item.items && item.items.length > 0) {
          printItems(item.items, indent + "  ");
        }
      });
    }

    if (menu.items) printItems(menu.items);
  });
}

getMenuDetails().catch(console.error);
