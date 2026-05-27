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

async function applyKitsConsolidation() {
  const plan = JSON.parse(fs.readFileSync("../../gre_kits_only_plan.json", "utf8"));
  const reportImages = JSON.parse(fs.readFileSync("gre_images_from_report.json", "utf8"));
  const imageMap: Record<string, string> = {};
  reportImages.forEach((img: any) => imageMap[img.sku] = img.image_url);

  console.log("🚀 AVVIO CONSOLIDAMENTO DEFINITIVO (SOLO KIT COMPLETI)...");

  // 1. PULIZIA TOTALE PISCINE GRE CONSOLIDATE PRECEDENTEMENTE
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
        if (p.title.includes("Piscina Gre")) {
            toDelete.push(p.id);
        }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`🗑️  Eliminazione di ${toDelete.length} prodotti per rifare i raggruppamenti puliti...`);
  for (const id of toDelete) {
      await shopifyRequest(`mutation { productDelete(input: { id: "${id}" }) { deletedProductId } }`);
  }

  // 2. CREAZIONE NUOVI PRODOTTI KIT
  const optionName = "Misura e Dotazione";
  
  for (const groupKey in plan) {
      const variants = plan[groupKey];
      const title = `Piscina Gre ${groupKey}`;
      
      console.log(`📦 Creazione Kit: ${title} (${variants.length} misure)`);

      const seenNames = new Set();
      const variantInputs = variants.map((v: any) => {
          let name = v.dim;
          if (seenNames.has(name)) {
              if (v.description.toLowerCase().includes("sabbia")) name += " - Sabbia";
              else if (v.description.toLowerCase().includes("cartuccia")) name += " - Cartuccia";
              else if (v.description.toLowerCase().includes("aqualoon")) name += " - Aqualoon";
              else name += ` (${v.sku})`;
          }
          if (seenNames.has(name)) name += ` - ${v.sku}`;
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
          if (imageMap[v.sku]) { bestImage = imageMap[v.sku]; break; }
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
              tags: ["Categoria:Piscine", "Listino:2026", "Tipo:Kit Completo"],
              productOptions: [{ name: optionName, values: uniqueOptions }],
              variants: variantInputs
          }
      });

      if (res.data?.productSet?.product) {
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
      }
  }

  console.log("\n✅ CONSOLIDAMENTO KIT COMPLETATO!");
}

applyKitsConsolidation().catch(console.error);
