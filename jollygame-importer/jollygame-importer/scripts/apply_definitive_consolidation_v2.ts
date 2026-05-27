import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  const data = await res.json();
  if (data.errors) {
      console.error("❌ Errore GraphQL:", JSON.stringify(data.errors, null, 2));
  }
  return data;
}

async function applyDefinitiveConsolidation() {
  const plan = JSON.parse(fs.readFileSync("../../gre_family_import_plan.json", "utf8"));
  const reportImages = JSON.parse(fs.readFileSync("gre_images_from_report.json", "utf8"));
  const imageMap: Record<string, string> = {};
  reportImages.forEach((img: any) => imageMap[img.sku] = img.image_url);

  console.log("🚀 AVVIO CONSOLIDAMENTO DEFINITIVO SERIE GRE...");

  const seriesFullNames = Object.keys(plan);
  
  for (const seriesFull of seriesFullNames) {
      const variants = plan[seriesFull];
      const seriesBase = seriesFull.split(' (')[0];
      const title = `Piscina Gre Serie ${seriesFull}`;
      
      console.log(`📦 Creazione: ${title} (${variants.length} varianti)`);

      const createRes = await shopifyRequest(`
      mutation productCreate($input: ProductInput!) {
        productCreate(input: $input) {
          product { id }
          userErrors { field message }
        }
      }
      `, {
          input: {
              title: title,
              vendor: "Gre",
              productType: "Piscina",
              status: "ACTIVE",
              tags: ["Categoria:Piscine", `Serie:${seriesBase}`, "Listino:2026"],
              productOptions: [{ name: "Misura" }]
          }
      });

      const productId = createRes.data?.productCreate?.product?.id;
      if (!productId) {
          console.error(`   ❌ Errore creazione ${title}:`, JSON.stringify(createRes.data?.productCreate?.userErrors, null, 2));
          continue;
      }

      const variantInputs = variants.map((v: any) => ({
          inventoryItem: { sku: v.sku },
          price: v.price,
          optionValues: [{ name: v.dim, optionName: "Misura" }],
          inventoryPolicy: "CONTINUE"
      }));

      const addVarRes = await shopifyRequest(`
      mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
        productVariantsBulkCreate(productId: $productId, variants: $variants) {
          userErrors { field message }
        }
      }
      `, {
          productId: productId,
          variants: variantInputs
      });

      if (addVarRes.data?.productVariantsBulkCreate?.userErrors?.length) {
          console.error(`   ❌ Errore varianti ${title}:`, addVarRes.data.productVariantsBulkCreate.userErrors);
      } else {
          console.log(`   ✅ Varianti aggiunte.`);
          
          let bestImage = null;
          for (const v of variants) {
              if (imageMap[v.sku]) {
                  bestImage = imageMap[v.sku];
                  break;
              }
          }

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
      }
  }

  console.log("\n✅ CONSOLIDAMENTO DEFINITIVO COMPLETATO.");
}

applyDefinitiveConsolidation().catch(console.error);
