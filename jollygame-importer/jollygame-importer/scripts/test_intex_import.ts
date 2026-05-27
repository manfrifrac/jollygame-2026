import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

if (!SHOP_DOMAIN || !ACCESS_TOKEN) {
  console.error("Missing SHOP_DOMAIN or SHOPIFY_ACCESS_TOKEN in .env");
  process.exit(1);
}

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

const PRODUCT_CREATE = `
mutation productCreate($input: ProductInput!) {
  productCreate(input: $input) {
    product { id title handle }
    userErrors { field message }
  }
}
`;

const PRODUCT_VARIANT_CREATE = `
mutation productVariantCreate($input: ProductVariantInput!) {
  productVariantCreate(input: $input) {
    productVariant { id }
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

async function runTestImport() {
  const csvPath = path.resolve("../../gold_intex_final.csv");
  const content = fs.readFileSync(csvPath, "utf-8");
  const records = parse(content, { columns: true, skip_empty_lines: true }).slice(0, 3);

  console.log(`🧪 Avvio Test Importazione per ${records.length} prodotti Intex...`);

  for (const record of records) {
    const title = record.Titolo;
    const vendor = "Intex";
    const tags = record.Tags.split(",");
    const descriptionHtml = record.Descrizione_HTML;
    const price = record.Prezzo.replace(",", ".");
    const sku = record.SKU;
    const ean = record.EAN;

    console.log(`\n📦 Creazione: ${title}`);
    
    // 1. Create Product
    const prodRes = await shopifyRequest(PRODUCT_CREATE, {
      input: {
        title,
        descriptionHtml,
        vendor,
        tags,
        status: "DRAFT" // In bozza per controllo
      }
    });

    const productId = prodRes.data?.productCreate?.product?.id;
    if (!productId) {
      console.error("❌ Errore Prodotto:", prodRes.data?.productCreate?.userErrors);
      continue;
    }

    // 2. Create Variant with Price, SKU, EAN
    const varRes = await shopifyRequest(PRODUCT_VARIANT_CREATE, {
      input: {
        productId,
        price,
        sku,
        barcode: ean
      }
    });
    if (varRes.data?.productVariantCreate?.userErrors?.length > 0) {
        console.error("❌ Errore Variante:", varRes.data.productVariantCreate.userErrors);
    }

    // 3. Create Media
    const images = JSON.parse(record.Immagini_JSON || "[]");
    if (images.length > 0) {
      const mediaInput = images.slice(0, 5).map((url: string) => ({
        alt: title,
        mediaContentType: "IMAGE",
        originalSource: url
      }));
      
      console.log(`🖼️ Caricamento ${mediaInput.length} immagini...`);
      const mediaRes = await shopifyRequest(PRODUCT_CREATE_MEDIA, {
        productId,
        media: mediaInput
      });
      if (mediaRes.data?.productCreateMedia?.userErrors?.length > 0) {
          console.error("❌ Errore Media:", mediaRes.data.productCreateMedia.userErrors);
      }
    }

    console.log(`✅ Completato: ${title}`);
  }
}

runTestImport().catch(console.error);
