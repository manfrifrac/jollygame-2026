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

async function auditCollectionsForMegaMenu() {
  console.log("🔍 Avvio Audit Collezioni e Metafield per Mega Menu...");

  // 1. Verifichiamo Metafield Definition per COLLECTIONS e PRODUCTS
  const metaDefQuery = `
  {
    collectionMeta: metafieldDefinitions(first: 50, ownerType: COLLECTION) {
      nodes { namespace key name type { name } }
    }
    productMeta: metafieldDefinitions(first: 50, ownerType: PRODUCT) {
      nodes { namespace key name type { name } }
    }
  }
  `;

  const metaDefs = await shopifyRequest(metaDefQuery);
  console.log("\n📋 Metafield Definitions (Collezioni):");
  if (metaDefs.data?.collectionMeta?.nodes) {
    console.table(metaDefs.data.collectionMeta.nodes);
  } else {
    console.log("Nessuna definizione trovata.");
  }
  
  console.log("\n📋 Metafield Definitions (Prodotti):");
  if (metaDefs.data?.productMeta?.nodes) {
    console.table(metaDefs.data.productMeta.nodes);
  } else {
    console.log("Nessuna definizione trovata.");
  }

  // 2. Recuperiamo le Collezioni con Immagini e Metafield effettivi
  const collectionQuery = `
  {
    collections(first: 100) {
      nodes {
        id
        title
        handle
        image { url }
        metafields(first: 20) {
          nodes {
            namespace
            key
            value
          }
        }
      }
    }
  }
  `;

  const collections = await shopifyRequest(collectionQuery);
  console.log("\n📦 Stato Collezioni:");
  
  if (collections.data?.collections?.nodes) {
    const report = collections.data.collections.nodes.map((c: any) => ({
      Titolo: c.title,
      Handle: c.handle,
      Immagine: c.image ? "✅ Presente" : "❌ Mancante",
      Metafields: c.metafields.nodes.map((m: any) => `${m.namespace}.${m.key}`).join(", ") || "Nessuno"
    }));
    console.table(report);
  } else {
    console.log("Nessuna collezione trovata.");
  }
}

auditCollectionsForMegaMenu().catch(console.error);
