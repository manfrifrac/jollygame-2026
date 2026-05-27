import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function extremeDeduplicate() {
  console.log("🕵️ Inizio scansione pixel-per-pixel dei media...");
  
  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        media(first: 50) {
          nodes {
            id
            mediaContentType
            ... on MediaImage {
              image {
                width
                height
                url
              }
            }
          }
        }
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    products.push(...res.data.products.nodes);
    hasNext = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  let totalRemoved = 0;

  for (const product of products) {
    const images = product.media.nodes.filter((m: any) => m.mediaContentType === 'IMAGE');
    const seenDimensions = new Set();
    const toDelete: string[] = [];

    for (const img of images) {
        if (!img.image) continue;
        
        // Creiamo un hash basato sulle dimensioni esatte
        const dimensionHash = `${img.image.width}x${img.image.height}`;
        
        if (seenDimensions.has(dimensionHash)) {
            toDelete.push(img.id);
        } else {
            seenDimensions.add(dimensionHash);
        }
    }

    if (toDelete.length > 0) {
        totalRemoved += toDelete.length;
        console.log(`\n👯 [${product.title}] Trovate ${toDelete.length} immagini identiche per dimensioni. Rimozione...`);
        
        const delMutation = `
        mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
          productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
            deletedMediaIds
            userErrors { message }
          }
        }
        `;
        const delRes = await shopifyRequest(delMutation, { productId: product.id, mediaIds: toDelete });
        if (delRes.data?.productDeleteMedia?.userErrors?.length > 0) {
            console.error("  ❌ Errore durante l'eliminazione:", delRes.data.productDeleteMedia.userErrors);
        } else {
            process.stdout.write("🗑️");
        }
    }
  }

  console.log(`\n\n✨ Operazione conclusa. Rimosse ${totalRemoved} immagini duplicate fisicamente.`);
}

extremeDeduplicate().catch(console.error);
