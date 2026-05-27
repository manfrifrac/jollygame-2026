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

const csvFilePath = path.resolve("../../zodiac_enriched_data.csv");

const productCreateMutation = `
mutation productCreate($input: ProductInput!) {
  productCreate(input: $input) {
    product { id title }
    userErrors { field message }
  }
}
`;

const productVariantCreateMutation = `
mutation productVariantCreate($input: ProductVariantInput!) {
  productVariantCreate(input: $input) {
    productVariant { id }
    userErrors { field message }
  }
}
`;

const productCreateMediaMutation = `
mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
  productCreateMedia(media: $media, productId: $productId) {
    media { id }
    userErrors { field message }
  }
}
`;

const metaobjectCreateMutation = `
mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
  metaobjectCreate(metaobject: $metaobject) {
    metaobject { id }
    userErrors { field message }
  }
}
`;

const productUpdateMutation = `
mutation productUpdate($input: ProductInput!) {
  productUpdate(input: $input) {
    product { id }
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

async function importProducts() {
  const content = fs.readFileSync(csvFilePath, "utf-8");
  const records = parse(content, { columns: true, skip_empty_lines: true });

  console.log(`🚀 Avvio importazione di ${records.length} prodotti.`);

  for (const record of records) {
    const title = record.Titolo || "Senza Titolo";
    const descriptionHtml = record.Descrizione_HTML || "";
    const tags = record.Tags ? record.Tags.split(",").map((t: string) => t.trim()) : [];
    
    // 1. Creazione Prodotto con Metafield Base
    const metafields = [];
    if (record.Sottotitolo) {
      metafields.push({ namespace: "custom", key: "short_description", type: "single_line_text_field", value: record.Sottotitolo });
      metafields.push({ namespace: "global", key: "description_tag", type: "string", value: record.Sottotitolo });
    }
    if (record.Caratteristiche) {
      metafields.push({ namespace: "custom", key: "additional_specs", type: "json", value: JSON.stringify(record.Caratteristiche.split("\n")) });
    }

    console.log(`\n📦 [${title}] Step 1: Creazione Prodotto...`);
    const productRes = await shopifyRequest(productCreateMutation, {
      input: { title, descriptionHtml, vendor: "Zodiac", tags, status: "DRAFT", metafields }
    });

    const productId = productRes.data?.productCreate?.product?.id;
    if (!productId) {
      console.error(`❌ Errore creazione prodotto:`, productRes.data?.productCreate?.userErrors);
      continue;
    }

    // 2. Creazione Variante
    let price = record.Prezzo ? record.Prezzo.replace(/[^\d.,]/g, "").replace(",", ".") : "0.00";
    await shopifyRequest(productVariantCreateMutation, {
      input: { productId, price, sku: record.URL.split("/").pop() }
    });

    // 3. Creazione Media (Immagini + Video YouTube)
    const media = [];
    if (record.Immagini) {
      record.Immagini.split(",").map((url: string) => ({
        alt: title, mediaContentType: "IMAGE", originalSource: url.trim()
      })).slice(0, 6).forEach(m => media.push(m));
    }
    if (record.YouTube_Videos) {
      record.YouTube_Videos.split(",").forEach((url: string) => {
        media.push({ alt: title, mediaContentType: "EXTERNAL_VIDEO", originalSource: url.trim() });
      });
    }
    
    if (media.length > 0) {
      console.log(`🖼️ [${title}] Step 2: Caricamento Media...`);
      await shopifyRequest(productCreateMediaMutation, { productId, media });
    }

    // 4. Gestione PDF (Metaobjects)
    if (record.PDF_Documents) {
      console.log(`📄 [${title}] Step 3: Gestione PDF...`);
      const docIds = [];
      const pdfs = record.PDF_Documents.split(",").map((p: string) => p.trim());
      
      for (const pdf of pdfs) {
        const [label, url] = pdf.includes("|") ? pdf.split("|") : ["Documento Tecnico", pdf];
        const moRes = await shopifyRequest(metaobjectCreateMutation, {
          metaobject: {
            type: "documento_tecnico",
            fields: [
              { key: "titolo", value: label },
              { key: "url_file", value: url }
            ]
          }
        });
        if (moRes.data?.metaobjectCreate?.metaobject?.id) {
          docIds.push(moRes.data.metaobjectCreate.metaobject.id);
        }
      }

      if (docIds.length > 0) {
        await shopifyRequest(productUpdateMutation, {
          input: {
            id: productId,
            metafields: [{
              namespace: "custom",
              key: "documentazione_tecnica",
              value: JSON.stringify(docIds)
            }]
          }
        });
      }
    }

    console.log(`✅ [${title}] Importato con successo.`);
    await new Promise(r => setTimeout(r, 1000));
  }
}

importProducts().catch(console.error);
