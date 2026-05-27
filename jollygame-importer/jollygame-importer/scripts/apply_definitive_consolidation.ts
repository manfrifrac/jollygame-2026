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

async function applyDefinitiveConsolidation() {
  const plan = JSON.parse(fs.readFileSync("../../gre_family_import_plan.json", "utf8"));
  const reportImages = JSON.parse(fs.readFileSync("gre_images_from_report.json", "utf8"));
  const imageMap: Record<string, string> = {};
  reportImages.forEach((img: any) => imageMap[img.sku] = img.image_url);

  console.log("🚀 AVVIO CONSOLIDAMENTO DEFINITIVO SERIE GRE...");

  // 1. ELIMINAZIONE PRODOTTI ESISTENTI (Per pulizia totale)
  // Cerchiamo prodotti che contengono nomi delle serie
  const seriesNames = Object.keys(plan).map(k => k.split(' (')[0]);
  
  let hasNextPage = true;
  let cursor = null;
  const toDelete: string[] = [];

  while (hasNextPage) {
    const query = `
    query getOld($cursor: String) {
      products(first: 250, after: $cursor, query: "vendor:Gre") {
        pageInfo { hasNextPage endCursor }
        nodes { id title }
      }
    }
    `;
    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;
    
    for (const p of res.data.products.nodes) {
        const title = p.title.toLowerCase();
        if (seriesNames.some(sn => title.includes(sn.toLowerCase())) || title.includes("piscina gre serie")) {
            toDelete.push(p.id);
        }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`🗑️  Eliminazione di ${toDelete.length} prodotti obsoleti...`);
  for (const id of toDelete) {
      await shopifyRequest(`mutation { productDelete(input: { id: "${id}" }) { deletedProductId } }`);
  }

  // 2. CREAZIONE NUOVE SERIE
  for (const seriesFull in plan) {
      const variants = plan[seriesFull];
      const seriesBase = seriesFull.split(' (')[0];
      const title = `Piscina Gre Serie ${seriesFull}`;
      
      console.log(`📦 Creazione: ${title} (${variants.length} varianti)`);

      // Create Product
      const createMutation = `
      mutation productCreate($input: ProductInput!) {
        productCreate(input: $input) {
          product { id }
          userErrors { message }
        }
      }
      `;

      const createRes = await shopifyRequest(createMutation, {
          input: {
              title: title,
              vendor: "Gre",
              productType: "Piscina",
              status: "ACTIVE",
              tags: ["Categoria:Piscine", `Serie:${seriesBase}`, "Listino:2026"],
              options: ["Misura"]
          }
      });

      const productId = createRes.data?.productCreate?.product?.id;
      if (!productId) {
          console.error(`   ❌ Errore creazione ${title}:`, createRes.data?.productCreate?.userErrors);
          continue;
      }

      // Add Variants
      const variantInputs = variants.map((v: any) => ({
          inventoryItem: { sku: v.sku },
          price: v.price,
          optionValues: [{ name: v.dim, optionName: "Misura" }],
          inventoryPolicy: "CONTINUE"
      }));

      const addVarRes = await shopifyRequest(`
      mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
        productVariantsBulkCreate(productId: $productId, variants: $variants) {
          productVariants { id }
          userErrors { message }
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
          
          // 3. ASSOCIAZIONE IMMAGINE (Usa la prima disponibile tra gli SKU)
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

  console.log("\n✅ CONSOLIDAMENTO DEFINITIVO COMPLETATO CON SUCCESSO.");
}

applyDefinitiveConsolidation().catch(console.error);
