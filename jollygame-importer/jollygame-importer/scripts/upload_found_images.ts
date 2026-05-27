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

async function uploadFoundImages() {
  const images = JSON.parse(fs.readFileSync("gre_images_from_report.json", "utf8"));
  console.log(`🚀 Avvio caricamento di ${images.length} immagini su Shopify...`);

  let count = 0;
  for (const img of images) {
      // 1. Create Media from URL
      const mutation = `
      mutation productCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
        productCreateMedia(productId: $productId, media: $media) {
          media { id status }
          userErrors { message }
        }
      }
      `;

      const res = await shopifyRequest(mutation, {
          productId: img.id,
          media: [
              {
                  originalSource: img.image_url,
                  mediaContentType: "IMAGE"
              }
          ]
      });

      if (res.data?.productCreateMedia?.media) {
          count++;
          if (count % 20 === 0) console.log(`   - Caricate ${count} immagini...`);
      } else {
          console.error(`   ❌ Errore caricamento per ${img.sku}:`, res.data?.productCreateMedia?.userErrors);
      }
  }

  console.log(`\n✅ Operazione completata. ${count} prodotti ora hanno una foto.`);
}

uploadFoundImages().catch(console.error);
