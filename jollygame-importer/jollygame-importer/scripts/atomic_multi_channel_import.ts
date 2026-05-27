import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

// Channel IDs found in check_publications.ts
const PUBLICATION_IDS = [
    "gid://shopify/Publication/346104496476", // Online Store
    "gid://shopify/Publication/346104562012", // POS
    "gid://shopify/Publication/346104594780", // Shop
    "gid://shopify/Publication/346730856796", // JollyGameProductionLeg
    "gid://shopify/Publication/348543517020", // Google & YouTube
    "gid://shopify/Publication/348614787420"  // Inbox
];

async function shopifyRequest(query: string, variables: any) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

const PRODUCT_SET = `
mutation productSet($input: ProductSetInput!) {
  productSet(input: $input) {
    product { id title handle }
    userErrors { field message }
  }
}
`;

const PUBLISHABLE_PUBLISH = `
mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $input) {
    userErrors { field message }
  }
}
`;

const PRODUCT_CREATE_MEDIA = `
mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
  productCreateMedia(media: $media, productId: $productId) {
    media { id }
    userErrors { field message }
  }
}
`;

async function runAtomicImport() {
  const csvPath = path.resolve("../../gold_consolidated_final.csv");
  const content = fs.readFileSync(csvPath, "utf-8");
  const records = parse(content, { columns: true, skip_empty_lines: true });

  // 1. Group ONLY Pools/SPA
  const masterGroups: Record<string, any[]> = {};
  for (const record of records) {
    if (record.Tags.toLowerCase().includes("piscine")) {
        if (!masterGroups[record.Master_Title]) masterGroups[record.Master_Title] = [];
        masterGroups[record.Master_Title].push(record);
    }
  }

  const masterTitles = Object.keys(masterGroups);
  console.log(`🚀 Avvio Pubblicazione Atomica Multi-Canale per ${masterTitles.length} Famiglie di Piscine.`);

  for (const masterTitle of masterTitles) {
    const variants = masterGroups[masterTitle];
    console.log(`📦 Pubblicazione: ${masterTitle} (${variants.length} varianti)`);

    // Prepare ProductSet Input
    const generatedHandle = masterTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
    const productInput = {
      title: masterTitle,
      handle: generatedHandle,
      descriptionHtml: variants[0].Descrizione_HTML,
      vendor: variants[0].Tags.includes('Intex') ? 'Intex' : 'Bestway',
      productCategory: { gpcValue: "5423" }, // Swimming Pools
      status: "ACTIVE",
      tags: variants[0].Tags.split(','),
      productOptions: [{
          name: "Modello/Misura",
          values: Array.from(new Set(variants.map(v => ({ name: v.Variant_Detail || v.SKU }))))
      }],
      variants: variants.map(v => ({
          price: v.Prezzo.replace(',', '.'),
          sku: v.SKU,
          barcode: (v.EAN && v.EAN !== 'None') ? v.EAN : null,
          optionValues: [{
              optionName: "Modello/Misura",
              name: v.Variant_Detail || v.SKU
          }]
      }))
    };

    // Step A: Create/Update Product with Variants
    const setRes = await shopifyRequest(PRODUCT_SET, { input: productInput });
    
    if (setRes.data?.productSet?.userErrors?.length > 0) {
        console.error(`  ❌ Error:`, JSON.stringify(setRes.data.productSet.userErrors, null, 2));
        continue;
    }

    const productId = setRes.data?.productSet?.product?.id;
    const handle = setRes.data?.productSet?.product?.handle;

    // Step B: Publish to all 6 channels
    await shopifyRequest(PUBLISHABLE_PUBLISH, {
        id: productId,
        input: PUBLICATION_IDS.map(pubId => ({ publicationId: pubId }))
    });

    // Step C: Media
    let images = [];
    try {
        let imgStr = variants[0].Immagini_JSON || "[]";
        if (imgStr.startsWith('"[') && imgStr.endsWith(']"')) {
            imgStr = imgStr.slice(1, -1).replace(/""/g, '"');
        } else if (imgStr.startsWith('[') && !imgStr.includes('"')) {
             imgStr = imgStr.replace(/\[|\]/g, '').split(',').map((s: string) => s.trim()).filter((s: string) => s.startsWith('http'));
             images = imgStr as any;
        }
        if (typeof imgStr === 'string') {
            images = JSON.parse(imgStr);
        }
    } catch (e) {
        console.warn(`  ⚠️ Impossibile parsare le immagini per ${masterTitle}. Procedo senza media.`);
        images = [];
    }

    if (images.length > 0) {
        const mediaInput = images.slice(0, 5).map((url: string) => ({
            alt: masterTitle,
            mediaContentType: "IMAGE",
            originalSource: url
        }));
        await shopifyRequest(PRODUCT_CREATE_MEDIA, { productId, media: mediaInput });
    }

    console.log(`  ✅ Live su tutti i canali: https://${SHOP_DOMAIN}/products/${handle}`);
    
    await new Promise(r => setTimeout(r, 1500));
  }
}

runAtomicImport().catch(console.error);
