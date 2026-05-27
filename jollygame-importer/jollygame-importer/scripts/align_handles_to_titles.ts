import dotenv from "dotenv";
import fs from "fs";

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

function slugify(text: string) {
  return text
    .toString()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

async function alignHandles() {
  console.log("🔄 Allineamento Handle a Titoli e creazione Redirect...");

  const query = `
  {
    products(first: 250, query: "status:active") {
      nodes {
        id
        title
        handle
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  for (const product of products) {
    const newHandle = slugify(product.title);
    
    if (newHandle !== product.handle) {
      console.log(`\n📦 Prodotto: ${product.title}`);
      console.log(`   - Vecchio Handle: ${product.handle}`);
      console.log(`   - Nuovo Handle:   ${newHandle}`);

      // 1. Creazione Redirect
      const redirectMutation = `
      mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
        urlRedirectCreate(urlRedirect: $urlRedirect) {
          urlRedirect { id path target }
          userErrors { message }
        }
      }
      `;

      const redirectRes = await shopifyRequest(redirectMutation, {
        urlRedirect: {
          path: `/products/${product.handle}`,
          target: `/products/${newHandle}`
        }
      });

      if (redirectRes.data?.urlRedirectCreate?.userErrors?.length > 0) {
          console.error(`   ❌ Errore Redirect:`, redirectRes.data.urlRedirectCreate.userErrors);
      } else {
          console.log(`   ✅ Redirect creato con successo.`);
      }

      // 2. Aggiornamento Handle
      const updateRes = await shopifyRequest(`
        mutation {
          productUpdate(input: { id: "${product.id}", handle: "${newHandle}" }) {
            product { id handle }
            userErrors { message }
          }
        }
      `);

      if (updateRes.data?.productUpdate?.userErrors?.length > 0) {
          console.error(`   ❌ Errore Handle:`, updateRes.data.productUpdate.userErrors);
      } else {
          console.log(`   ✅ Handle aggiornato.`);
      }
    }
  }

  console.log("\n🎉 Allineamento completato!");
}

alignHandles().catch(console.error);
