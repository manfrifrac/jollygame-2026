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

async function applyDefinitiveConsolidationV3() {
  const plan = JSON.parse(fs.readFileSync("../../gre_family_import_plan.json", "utf8"));
  const reportImages = JSON.parse(fs.readFileSync("gre_images_from_report.json", "utf8"));
  const imageMap: Record<string, string> = {};
  reportImages.forEach((img: any) => imageMap[img.sku] = img.image_url);

  console.log("🚀 AVVIO CONSOLIDAMENTO DEFINITIVO SERIE GRE (VIA PRODUCT SET)...");

  for (const seriesFull in plan) {
      const variants = plan[seriesFull];
      const seriesBase = seriesFull.split(' (')[0];
      const title = `Piscina Gre Serie ${seriesFull}`;
      
      console.log(`📦 Creazione/Aggiornamento: ${title} (${variants.length} varianti)`);

      // Prepare variants for productSet
      const variantInputs = variants.map((v: any) => ({
          inventoryItem: { sku: v.sku },
          price: v.price,
          optionValues: [{ name: v.dim, optionName: "Misura" }],
          inventoryPolicy: "CONTINUE"
      }));

      // Find cover image
      let bestImage = null;
      for (const v of variants) {
          if (imageMap[v.sku]) {
              bestImage = imageMap[v.sku];
              break;
          }
      }

      const productSetMutation = `
      mutation productSet($input: ProductSetInput!) {
        productSet(input: $input) {
          product { id }
          userErrors { field message }
        }
      }
      `;

      const res = await shopifyRequest(productSetMutation, {
          input: {
              title: title,
              vendor: "Gre",
              productType: "Piscina",
              status: "ACTIVE",
              tags: ["Categoria:Piscine", `Serie:${seriesBase}`, "Listino:2026"],
              productOptions: [{ name: "Misura", values: [{ name: variants[0].dim }] }],
              variants: variantInputs
          }
      });

      if (res.data?.productSet?.product) {
          const productId = res.data.productSet.product.id;
          console.log(`   ✅ Prodotto impostato correttamente.`);
          
          if (bestImage) {
              await shopifyRequest(`
              mutation productCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
                productCreateMedia(productId: $productId, media: $media) { media { id } }
              }
              `, {
                  productId: productId,
                  media: [{ originalSource: bestImage, mediaContentType: "IMAGE" }]
              });
              console.log(`   🖼️  Immagine caricata.`);
          }
      } else {
          console.error(`   ❌ Errore productSet ${title}:`, JSON.stringify(res.data?.productSet?.userErrors || res.errors, null, 2));
      }
  }

  console.log("\n✅ OPERAZIONE COMPLETATA.");
}

applyDefinitiveConsolidationV3().catch(console.error);
