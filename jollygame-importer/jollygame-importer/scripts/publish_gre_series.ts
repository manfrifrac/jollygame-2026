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

async function publishAllGreSeries() {
  console.log("🔓 Pubblicazione Serie Gre sul Negozio Online...");

  // 1. Trova l'ID della pubblicazione "Online Store"
  const pubQuery = `{
    publications(first: 10) {
      nodes { id name }
    }
  }`;
  const pubRes = await shopifyRequest(pubQuery);
  const onlineStorePub = pubRes.data.publications.nodes.find((p: any) => p.name === "Online Store");

  if (!onlineStorePub) {
      console.error("❌ Canale Online Store non trovato.");
      return;
  }

  const pubId = onlineStorePub.id;
  console.log(`📡 Canale Online Store ID: ${pubId}`);

  // 2. Trova tutti i prodotti Gre
  const prodQuery = `{
    products(first: 250, query: "vendor:Gre") {
      nodes { id title }
    }
  }`;
  const prodRes = await shopifyRequest(prodQuery);
  const products = prodRes.data.products.nodes.filter((p: any) => p.title.includes("Piscina Gre"));

  console.log(`🚀 Pubblicazione di ${products.length} serie...`);

  for (const p of products) {
      const mutation = `
      mutation publishProduct($id: ID!, $input: [PublicationInput!]!) {
        publishablePublish(id: $id, input: $input) {
          userErrors { message }
        }
      }
      `;
      const res = await shopifyRequest(mutation, {
          id: p.id,
          input: [{ publicationId: pubId }]
      });

      if (!res.data?.publishablePublish?.userErrors?.length) {
          console.log(`   ✅ Pubblicato: ${p.title}`);
      } else {
          console.error(`   ❌ Errore ${p.title}:`, res.data.publishablePublish.userErrors);
      }
  }

  console.log("\n✅ TUTTI I PRODOTTI SONO ORA VISIBILI ONLINE.");
}

publishAllGreSeries().catch(console.error);
