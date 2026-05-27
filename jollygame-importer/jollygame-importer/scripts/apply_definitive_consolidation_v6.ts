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

async function applyDefinitiveConsolidationV6() {
  const plan = JSON.parse(fs.readFileSync("../../gre_family_import_plan.json", "utf8"));
  const reportImages = JSON.parse(fs.readFileSync("gre_images_from_report.json", "utf8"));
  const imageMap: Record<string, string> = {};
  reportImages.forEach((img: any) => imageMap[img.sku] = img.image_url);

  console.log("🚀 AVVIO CONSOLIDAMENTO DEFINITIVO SERIE GRE (V6 - NO SLASHES)...");

  for (const seriesFull in plan) {
      const variants = plan[seriesFull];
      const seriesBase = seriesFull.split(' (')[0];
      const title = `Piscina Gre Serie ${seriesFull}`;
      const optionName = "Dimensione e Dotazione";
      
      console.log(`📦 Creazione/Aggiornamento: ${title} (${variants.length} varianti)`);

      const seenNames = new Set();
      const variantInputs = variants.map((v: any) => {
          let name = v.dim.replace('/', '-'); // Evita slash anche nei valori
          if (seenNames.has(name)) {
              if (v.description.toLowerCase().includes("sabbia")) name += " - Sabbia";
              else if (v.description.toLowerCase().includes("cartuccia")) name += " - Cartuccia";
              else if (v.description.toLowerCase().includes("aqualoon")) name += " - Aqualoon";
              else name += ` - ${v.sku}`;
          }
          if (seenNames.has(name)) { name += ` (${v.sku})`; }
          
          seenNames.add(name);
          return {
              inventoryItem: { sku: v.sku },
              price: v.price,
              optionValues: [{ name: name, optionName: optionName }],
              inventoryPolicy: "CONTINUE"
          };
      });

      const uniqueOptions = [...seenNames].map(n => ({ name: n }));

      let bestImage = null;
      for (const v of variants) {
          if (imageMap[v.sku]) {
              bestImage = imageMap[v.sku];
              break;
          }
      }

      const res = await shopifyRequest(`
      mutation productSet($input: ProductSetInput!) {
        productSet(input: $input) {
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
              productOptions: [{ name: optionName, values: uniqueOptions }],
              variants: variantInputs
          }
      });

      if (res.data?.productSet?.product) {
          console.log(`   ✅ Prodotto "${title}" impostato.`);
          if (bestImage) {
              await shopifyRequest(`
              mutation productCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
                productCreateMedia(productId: $productId, media: $media) { media { id } }
              }
              `, {
                  productId: res.data.productSet.product.id,
                  media: [{ originalSource: bestImage, mediaContentType: "IMAGE" }]
              });
          }
      } else {
          console.error(`   ❌ Errore productSet ${title}:`, JSON.stringify(res.data?.productSet?.userErrors || res.errors, null, 2));
      }
  }

  console.log("\n✅ OPERAZIONE COMPLETATA CON SUCCESSO.");
}

applyDefinitiveConsolidationV6().catch(console.error);
