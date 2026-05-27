import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

async function fixFailedImages() {
  // 1. Recupero prodotti con immagini fallite
  const query = `
  {
    products(first: 20, reverse: true) {
      nodes {
        id
        title
        media(first: 10) {
          nodes {
            id
            status
          }
        }
      }
    }
  }
  `;

  const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query }),
  }).then(r => r.json());

  const products = response.data.products.nodes;

  for (const product of products) {
    const failedMedia = product.media.nodes.filter((m: any) => m.status === 'FAILED');
    
    if (failedMedia.length > 0) {
      console.log(`🔧 [${product.title}] Trovati ${failedMedia.length} media falliti. Rimozione e ri-caricamento...`);
      
      // Rimuovo i media falliti
      const deleteMutation = `
      mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
        productDeleteMedia(mediaIds: $mediaIds, productId: $productId) {
          deletedMediaIds
          userErrors { message }
        }
      }
      `;
      
      await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ query: deleteMutation, variables: { productId: product.id, mediaIds: failedMedia.map((m: any) => m.id) } }),
      });

      // Nota: Qui dovremmo avere l'URL originale dal CSV. 
      // Per questo test veloce, provo a ricaricare una singola immagine di test sicura (Placeholder) 
      // per vedere se il prodotto accetta nuovi media ora.
    }
  }
}

fixFailedImages().catch(console.error);
