import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import mime from "mime-types";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

const PRODUCT_BY_HANDLE = `query getProduct($handle: String!) { productByHandle(handle: $handle) { id title variants(first: 1) { nodes { id price } } } }`;
const PUBLISHABLE_PUBLISH = `mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) { publishablePublish(id: $id, input: $input) { userErrors { message } } }`;
const PUBLISHABLE_UNPUBLISH = `mutation publishableUnpublish($id: ID!, $input: [PublicationInput!]!) { publishableUnpublish(id: $id, input: $input) { userErrors { message } } }`;

async function shopifyRequest(query: string, variables: any) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function getPublications() {
  const res = await shopifyRequest(`{ publications(first: 50) { nodes { id name } } }`, {});
  return res.data?.publications?.nodes || [];
}

async function resolveAndPublish() {
  console.log("🔍 Inizio bonifica duplicati e canali di vendita...");
  const publications = await getPublications();
  const googleChannel = publications.find((p: any) => p.name.toLowerCase().includes("google"));
  const youtubeChannel = publications.find((p: any) => p.name.toLowerCase().includes("youtube"));

  // Recupero tutti i prodotti caricati finora (fino a 250)
  const productsQuery = `{ products(first: 250) { nodes { id title handle variants(first: 1) { nodes { price } } } } }`;
  const prodRes = await shopifyRequest(productsQuery, {});
  const products = prodRes.data.products.nodes;

  for (const product of products) {
    const price = parseFloat(product.variants.nodes[0]?.price || "0");
    const hasPrice = price > 0;

    console.log(`\n📦 [${product.title}] Prezzo: €${price}`);

    const pubToApply = publications.map((p: any) => ({ publicationId: p.id }));
    const pubToRemove = [];

    if (!hasPrice) {
      if (googleChannel) pubToRemove.push({ publicationId: googleChannel.id });
      if (youtubeChannel) pubToRemove.push({ publicationId: youtubeChannel.id });
    }

    // 1. Pubblica ovunque
    await shopifyRequest(PUBLISHABLE_PUBLISH, { id: product.id, input: pubToApply });

    // 2. Rimuovi dai canali social se non c'è prezzo
    if (pubToRemove.length > 0) {
      console.log(`  🚫 Rimozione da Google/YouTube (Prezzo 0)`);
      await shopifyRequest(PUBLISHABLE_UNPUBLISH, { id: product.id, input: pubToRemove });
    } else {
      console.log(`  ✅ Pubblicato su tutti i canali`);
    }
  }

  console.log("\n✨ Operazione completata con successo.");
}

resolveAndPublish().catch(console.error);
