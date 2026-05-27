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

async function cleanupAndSetup() {
  console.log("🚀 Avvio Bonifica Collezioni e Setup Metafield...");

  // 1. CREAZIONE METAFIELD DEFINITION PER COLLEZIONI
  const createMetafieldQuery = `
  mutation {
    metafieldDefinitionCreate(definition: {
      name: "Prodotto in Evidenza (Menu)"
      namespace: "custom"
      key: "featured_product"
      ownerType: COLLECTION
      type: "product_reference"
      description: "Seleziona il prodotto da mostrare nel Mega Menu per questa categoria."
    }) {
      createdDefinition {
        id
        name
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  const metaRes = await shopifyRequest(createMetafieldQuery);
  if (metaRes.data?.metafieldDefinitionCreate?.createdDefinition) {
    console.log("✅ Metafield 'custom.featured_product' creato con successo.");
  } else {
    const error = metaRes.data?.metafieldDefinitionCreate?.userErrors[0]?.message;
    if (error?.includes("already exists")) {
        console.log("ℹ️ Metafield 'custom.featured_product' già esistente.");
    } else {
        console.error("❌ Errore creazione metafield:", error);
    }
  }

  // 2. RECUPERO COLLEZIONI DUPLICATE
  const getCollectionsQuery = `
  {
    collections(first: 100) {
      nodes {
        id
        handle
      }
    }
  }
  `;

  const colRes = await shopifyRequest(getCollectionsQuery);
  const allCollections = colRes.data?.collections?.nodes || [];

  const toDelete = allCollections.filter((c: any) => 
    c.handle.endsWith("-1") || 
    c.handle.endsWith("-2") || 
    c.handle.endsWith("-3")
  );

  if (toDelete.length === 0) {
    console.log("✨ Nessuna collezione duplicata trovata da eliminare.");
  } else {
    console.log(`🗑️ Eliminazione di ${toDelete.length} collezioni duplicate...`);
    for (const col of toDelete) {
      const deleteMutation = `
      mutation {
        collectionDelete(input: { id: "${col.id}" }) {
          deletedCollectionId
          userErrors {
            field
            message
          }
        }
      }
      `;
      const delRes = await shopifyRequest(deleteMutation);
      if (delRes.data?.collectionDelete?.deletedCollectionId) {
        console.log(`  ✅ Eliminata: ${col.handle}`);
      } else {
        console.error(`  ❌ Errore eliminazione ${col.handle}:`, delRes.data?.collectionDelete?.userErrors[0]?.message);
      }
    }
  }

  console.log("\n✨ Operazione completata.");
}

cleanupAndSetup().catch(console.error);
