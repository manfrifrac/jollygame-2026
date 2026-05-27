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

async function aggressiveDeduplicate() {
  console.log("🧼 Inizio pulizia media duplicati...");
  
  const query = `{
    products(first: 250) {
      nodes {
        id
        title
        media(first: 30) {
          nodes {
            id
            mediaContentType
            ... on MediaImage {
              image {
                url
                width
                height
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
    const seenHashes = new Set();
    const toDelete: string[] = [];

    for (const img of images) {
      // Identifichiamo l'immagine tramite dimensioni + nome file nell'URL
      const fileName = img.image?.url?.split('/').pop()?.split('?')[0];
      const hash = `${fileName}_${img.image?.width}x${img.image?.height}`;
      
      if (seenHashes.has(hash)) {
        toDelete.push(img.id);
      } else {
        seenHashes.add(hash);
      }
    }

    if (toDelete.length > 0) {
      console.log(`\n👯 [${product.title}] Rimozione di ${toDelete.length} immagini duplicate.`);
      const delMutation = `
      mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
        productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
          userErrors { message }
        }
      }
      `;
      await shopifyRequest(delMutation, { productId: product.id, mediaIds: toDelete });
      process.stdout.write("🗑️");
    }
  }
  console.log("\n\n✅ Galleria immagini ripulita.");
}

aggressiveDeduplicate().catch(console.error);
