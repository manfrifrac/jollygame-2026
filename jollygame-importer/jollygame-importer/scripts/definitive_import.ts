import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";
import mime from "mime-types";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

if (!SHOP_DOMAIN || !ACCESS_TOKEN) {
  console.error("Missing SHOP_DOMAIN or SHOPIFY_ACCESS_TOKEN in .env");
  process.exit(1);
}

// Mutations & Queries
const PRODUCT_BY_HANDLE = `
query getProduct($handle: String!) {
  productByHandle(handle: $handle) {
    id
  }
}
`;

const STAGED_UPLOADS_CREATE = `
mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
  stagedUploadsCreate(input: $input) {
    stagedTargets {
      url
      resourceUrl
      parameters { name value }
    }
    userErrors { field message }
  }
}
`;

const PRODUCT_CREATE = `
mutation productCreate($input: ProductInput!) {
  productCreate(input: $input) {
    product { id title handle }
    userErrors { field message }
  }
}
`;

const PRODUCT_UPDATE = `
mutation productUpdate($input: ProductInput!) {
  productUpdate(input: $input) {
    product { id }
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

const PUBLISHABLE_PUBLISH = `
mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $input) {
    userErrors { field message }
  }
}
`;

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

async function uploadFile(filePath: string) {
  const fileName = path.basename(filePath);
  const fileSize = fs.statSync(filePath).size.toString();
  const fileMime = mime.lookup(filePath) || "image/jpeg";

  const stagedRes = await shopifyRequest(STAGED_UPLOADS_CREATE, {
    input: [{
      filename: fileName,
      mimeType: fileMime,
      resource: "PRODUCT_IMAGE",
      fileSize: fileSize
    }]
  });

  const target = stagedRes.data?.stagedUploadsCreate?.stagedTargets[0];
  if (!target) return null;

  const formData = new FormData();
  target.parameters.forEach((p: any) => formData.append(p.name, p.value));
  
  const fileBuffer = fs.readFileSync(filePath);
  const blob = new Blob([fileBuffer], { type: fileMime });
  formData.append("file", blob, fileName); // Must be last

  const uploadRes = await fetch(target.url, {
    method: "POST",
    body: formData
  });

  return uploadRes.ok ? target.resourceUrl : null;
}

async function getPublications() {
  const res = await shopifyRequest(`{ publications(first: 50) { nodes { id name } } }`, {});
  return res.data?.publications?.nodes || [];
}

function mapTaxonomy(vendor: string, originalTags: string[]) {
  const tags = [`Brand:${vendor}`];
  const lowerTags = originalTags.map(t => t.toLowerCase());
  if (vendor === "Zodiac") {
    if (lowerTags.some(t => t.includes("robot") || t.includes("pulitori"))) {
      tags.push("Categoria:Pulitori");
      if (lowerTags.some(t => t.includes("elettrici"))) tags.push("Sottocategoria:Pulitori elettrico");
    }
    if (lowerTags.some(t => t.includes("riscaldamento"))) tags.push("Categoria:Riscaldamento");
  } else {
    tags.push("Categoria:Piscine fuori terra");
  }
  return [...new Set(tags)];
}

async function runImport(vendor: string, csvFile: string, imageBaseDir: string) {
  const publications = await getPublications();
  const googleChannel = publications.find((p: any) => p.name.toLowerCase().includes("google"));
  
  const records = parse(fs.readFileSync(path.resolve(csvFile), "utf-8"), { columns: true, skip_empty_lines: true });

  for (const record of records) {
    const title = record.Titolo || "Senza Titolo";
    const handle = title.toLowerCase().replace(/[^\w\s-]/g, '').replace(/[\s-]+/g, '-');
    
    // Check if product exists
    const checkRes = await shopifyRequest(PRODUCT_BY_HANDLE, { handle });
    let productId = checkRes.data?.productByHandle?.id;

    const priceRaw = record.Prezzo ? record.Prezzo.toString() : "0.00";
    const price = priceRaw.replace(/[^\d.,]/g, "").replace(",", ".");
    const hasPrice = parseFloat(price) > 0;

    if (productId) {
      console.log(`⏩ [${title}] Already exists. Skipping creation.`);
      continue; 
    }

    console.log(`\n📦 [${title}] Creating...`);
    const tags = mapTaxonomy(vendor, record.Tags ? record.Tags.split(",") : []);
    const descriptionHtml = record.Descrizione_HTML || (record.Caratteristiche_Tecniche || "");
    
    const prodRes = await shopifyRequest(PRODUCT_CREATE, {
      input: { title, handle, descriptionHtml, vendor, tags, status: "ACTIVE" }
    });

    productId = prodRes.data?.productCreate?.product?.id;
    if (!productId) continue;

    await shopifyRequest(PRODUCT_VARIANT_CREATE, {
      input: { productId, price, sku: `${vendor[0]}-${handle.slice(0,10)}` }
    });

    // Images
    const productSlug = title.replace(/[^\w\s-]/g, '').replace(/[\s-]+/g, '_');
    const localDir = path.join(imageBaseDir, productSlug);
    if (fs.existsSync(localDir)) {
      const files = fs.readdirSync(localDir).filter(f => /\.(jpg|jpeg|png|webp)$/i.test(f)).slice(0, 3);
      const media = [];
      for (const file of files) {
        const stagedUrl = await uploadFile(path.join(localDir, file));
        if (stagedUrl) media.push({ alt: title, mediaContentType: "IMAGE", originalSource: stagedUrl });
      }
      if (media.length > 0) await shopifyRequest(PRODUCT_CREATE_MEDIA, { productId, media });
    }

    // Publish
    const pubInputs = publications
        .filter((p: any) => hasPrice || !p.name.toLowerCase().includes("google"))
        .map((p: any) => ({ publicationId: p.id }));
    await shopifyRequest(PUBLISHABLE_PUBLISH, { id: productId, input: pubInputs });

    await new Promise(r => setTimeout(r, 800));
  }
}

async function main() {
  await runImport("Zodiac", "../../zodiac_enriched_data.csv", "../../zodiac_images");
  await runImport("Piscine Laghetto", "../../laghetto_full_export_enriched.csv", "../../laghetto_images");
}

main().catch(console.error);
