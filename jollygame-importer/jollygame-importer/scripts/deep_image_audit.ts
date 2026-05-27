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

async function deepImageAudit() {
  console.log("🔍 Analisi profonda immagini duplicate...");
  
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

  let totalDupes = 0;

  for (const product of products) {
    const images = product.media.nodes.filter((m: any) => m.mediaContentType === 'IMAGE');
    const seenFiles = new Map(); // fileName -> id
    const toDelete = [];

    for (const img of images) {
        if (!img.image?.url) continue;
        
        // Estraiamo il nome del file originale dall'URL di Shopify (es: .../files/nomefile.jpg?v=...)
        const urlParts = img.image.url.split('/');
        const fileNameWithParams = urlParts[urlParts.length - 1];
        const fileName = fileNameWithParams.split('?')[0];

        if (seenFiles.has(fileName)) {
            toDelete.push(img.id);
        } else {
            seenFiles.set(fileName, img.id);
        }
    }

    if (toDelete.length > 0) {
        totalDupes += toDelete.length;
        console.log(`\n👯 [${product.title}] Trovate ${toDelete.length} immagini duplicate (Nome file: ${[...toDelete].length}). Eliminazione...`);
        
        const delMutation = `
        mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
          productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
            deletedMediaIds
            userErrors { message }
          }
        }
        `;
        await shopifyRequest(delMutation, { productId: product.id, mediaIds: toDelete });
        process.stdout.write("✂️");
    }
  }

  console.log(`\n\n✅ Audit completato. Totale immagini duplicate rimosse: ${totalDupes}`);
}

deepImageAudit().catch(console.error);
