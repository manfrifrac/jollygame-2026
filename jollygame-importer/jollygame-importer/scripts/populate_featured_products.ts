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

async function populateFeaturedProducts() {
  console.log("🚀 Selezione automatica Prodotti in Evidenza per le Collezioni...");

  // 1. Recupero tutte le collezioni attive (quelle pulite)
  const getCollectionsQuery = `
  {
    collections(first: 50) {
      nodes {
        id
        title
        handle
      }
    }
  }
  `;

  const colRes = await shopifyRequest(getCollectionsQuery);
  const collections = colRes.data?.collections?.nodes || [];

  for (const collection of collections) {
    console.log(`\n📂 Analisi collezione: ${collection.title} (${collection.handle})`);

    // 2. Cerco i prodotti all'interno della collezione che hanno Prezzo > 0 e almeno un'immagine
    const getProductsQuery = `
    query ($id: ID!) {
      collection(id: $id) {
        products(first: 50) {
          nodes {
            id
            title
            featuredImage { url }
            variants(first: 1) {
              nodes {
                price
              }
            }
          }
        }
      }
    }
    `;

    const prodRes = await shopifyRequest(getProductsQuery, { id: collection.id });
    const products = prodRes.data?.collection?.products?.nodes || [];

    // Filtro prodotti validi: Prezzo > 0 E Immagine presente
    const validProducts = products.filter((p: any) => {
      const price = parseFloat(p.variants.nodes[0]?.price || "0");
      return price > 0 && p.featuredImage?.url;
    });

    if (validProducts.length === 0) {
      console.log("  ⚠️ Nessun prodotto valido trovato (prezzo 0 o senza immagini).");
      continue;
    }

    // Ordino per prezzo decrescente per prendere il prodotto più "importante"
    validProducts.sort((a: any, b: any) => {
      const priceA = parseFloat(a.variants.nodes[0]?.price || "0");
      const priceB = parseFloat(b.variants.nodes[0]?.price || "0");
      return priceB - priceA;
    });

    const bestProduct = validProducts[0];
    console.log(`  ✨ Selezionato: ${bestProduct.title} (€${bestProduct.variants.nodes[0].price})`);

    // 3. Aggiorno il metafield della collezione
    const updateMetafieldMutation = `
    mutation collectionUpdate($input: CollectionInput!) {
      collectionUpdate(input: $input) {
        collection {
          id
        }
        userErrors {
          field
          message
        }
      }
    }
    `;

    const updateRes = await shopifyRequest(updateMetafieldMutation, {
      input: {
        id: collection.id,
        metafields: [
          {
            namespace: "custom",
            key: "featured_product",
            value: bestProduct.id
          }
        ]
      }
    });

    if (updateRes.data?.collectionUpdate?.collection) {
      console.log(`  ✅ Metafield aggiornato con successo.`);
    } else {
      console.error(`  ❌ Errore aggiornamento:`, updateRes.data?.collectionUpdate?.userErrors[0]?.message);
    }
  }

  console.log("\n✨ Popolamento prodotti in evidenza completato.");
}

populateFeaturedProducts().catch(console.error);
