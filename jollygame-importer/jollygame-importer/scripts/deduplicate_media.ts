import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function deduplicateImages() {
  console.log("🔍 Analisi media duplicati in corso...");
  
  const query = `{
    products(first: 250) {
      nodes {
        id
        title
        media(first: 20) {
          nodes {
            id
            mediaContentType
            ... on MediaImage {
              image {
                url
              }
            }
          }
        }
      }
    }
  }`;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;

  for (const product of products) {
    const images = product.media.nodes.filter((m: any) => m.mediaContentType === 'IMAGE');
    const seenUrls = new Set();
    const toDelete: string[] = [];

    for (const img of images) {
      // Usiamo l'URL dell'immagine (senza i parametri di ridimensionamento di Shopify) per il confronto
      const pureUrl = img.image?.url?.split('?')[0];
      if (seenUrls.has(pureUrl)) {
        toDelete.push(img.id);
      } else {
        seenUrls.add(pureUrl);
      }
    }

    if (toDelete.length > 0) {
      console.log(`\n👯 [${product.title}] Trovati ${toDelete.length} doppioni. Eliminazione...`);
      const delMutation = `
      mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
        productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
          deletedMediaIds
          userErrors { message }
        }
      }
      `;
      await shopifyRequest(delMutation, { productId: product.id, mediaIds: toDelete });
      process.stdout.write("✅");
    }
  }
  console.log("\n\n✨ Deduplicazione media completata.");
}

deduplicateImages().catch(console.error);
