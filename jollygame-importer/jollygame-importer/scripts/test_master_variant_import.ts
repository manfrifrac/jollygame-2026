import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  const json = await response.json();
  if (json.errors) {
      console.error("❌ GraphQL Top-level Errors:", JSON.stringify(json.errors, null, 2));
  }
  return json;
}

const PRODUCT_CREATE = `
mutation productCreate($input: ProductInput!) {
  productCreate(input: $input) {
    product { id title }
    userErrors { field message }
  }
}
`;

const PRODUCT_VARIANTS_BULK_CREATE = `
mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkCreate(productId: $productId, variants: $variants) {
    productVariants { id title }
    userErrors { field message }
  }
}
`;

const PRODUCT_CREATE_MEDIA = `
mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
  productCreateMedia(media: $media, productId: $productId) {
    media { id status }
    userErrors { field message }
  }
}
`;

async function runMasterTest() {
  const csvPath = path.resolve("../../gold_consolidated_final.csv");
  const content = fs.readFileSync(csvPath, "utf-8");
  const records = parse(content, { columns: true, skip_empty_lines: true });

  // Group by Master_Title
  const masterGroups: Record<string, any[]> = {};
  for (const record of records) {
      if (!masterGroups[record.Master_Title]) masterGroups[record.Master_Title] = [];
      masterGroups[record.Master_Title].push(record);
  }

  // Pick 2 masters for test
  const testMasters = Object.keys(masterGroups).slice(0, 2);

  for (const masterTitle of testMasters) {
    const variants = masterGroups[masterTitle];
    console.log(`\n🚀 Test Import Master: ${masterTitle} (${variants.length} varianti)`);

    // 1. Create Master Product with Options
    const prodRes = await shopifyRequest(PRODUCT_CREATE, {
      input: {
        title: masterTitle,
        descriptionHtml: variants[0].Descrizione_HTML,
        vendor: variants[0].Tags.includes('Intex') ? 'Intex' : 'Bestway',
        tags: variants[0].Tags.split(','),
        status: "DRAFT",
        productOptions: [
            {
                name: "Modello/Misura",
                values: Array.from(new Set(variants.map(v => v.Variant_Detail || v.SKU))).map(val => ({ name: val }))
            }
        ]
      }
    });

    if (prodRes.data?.productCreate?.userErrors?.length > 0) {
        console.error("❌ Product Create User Errors:", JSON.stringify(prodRes.data.productCreate.userErrors, null, 2));
        continue;
    }

    const productId = prodRes.data?.productCreate?.product?.id;
    if (!productId) {
      console.error("❌ Failed to get Product ID. Full Response:", JSON.stringify(prodRes, null, 2));
      continue;
    }

    console.log(`✅ Prodotto Master creato. ID: ${productId}`);

    // 2. Add Variants in Bulk
    const variantInputs = variants.map(v => ({
        price: v.Prezzo.replace(',', '.'),
        inventoryItem: {
            sku: v.SKU
        },
        barcode: (v.EAN && v.EAN !== 'None') ? v.EAN : null,
        optionValues: [{
            optionName: "Modello/Misura",
            name: v.Variant_Detail || v.SKU
        }]
    }));

    const varRes = await shopifyRequest(PRODUCT_VARIANTS_BULK_CREATE, {
        productId,
        variants: variantInputs,
        strategy: "REMOVE_STANDALONE_VARIANT"
    });

    if (varRes.data?.productVariantsBulkCreate?.userErrors?.length > 0) {
        console.error("❌ Bulk Variant Create Errors:", JSON.stringify(varRes.data.productVariantsBulkCreate.userErrors, null, 2));
    } else {
        console.log(`✅ Aggiunte ${variants.length} varianti in bulk.`);
    }

    // 3. Media (from first variant)
    const images = JSON.parse(variants[0].Immagini_JSON || "[]");
    if (images.length > 0) {
        const mediaInput = images.slice(0, 3).map((url: string) => ({
            alt: masterTitle,
            mediaContentType: "IMAGE",
            originalSource: url
        }));
        const mediaRes = await shopifyRequest(PRODUCT_CREATE_MEDIA, { productId, media: mediaInput });
        if (mediaRes.data?.productCreateMedia?.userErrors?.length > 0) {
            console.error("❌ Media Error:", mediaRes.data.productCreateMedia.userErrors);
        } else {
            console.log(`  🖼️ Immagini collegate.`);
        }
    }
    
    console.log(`✨ Successo: ${masterTitle}`);
  }
}

runMasterTest().catch(console.error);
