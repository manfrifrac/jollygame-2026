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

const csvFilePath = path.resolve("../../laghetto_full_export_enriched.csv");

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

function cleanText(text: string) {
  if (!text) return "";
  return text.replace(/\n/g, " ").replace(/\s+/g, " ").trim();
}

async function importLaghetto() {
  if (!fs.existsSync(csvFilePath)) {
    console.error(`CSV file not found at ${csvFilePath}`);
    return;
  }

  const content = fs.readFileSync(csvFilePath, "utf-8");
  const records = parse(content, { columns: true, skip_empty_lines: true });

  console.log(`🚀 Avvio importazione Laghetto: ${records.length} prodotti.`);

  for (const record of records) {
    const title = record.Titolo || "Senza Titolo";
    const descriptionHtml = (record.Caratteristiche_Tecniche || "") + (record.Scheda_Tecnica_Dati || "") + (record.Descrizione_Manutenzione || "");
    
    // Tassonomia: Mapping Laghetto -> JollyGame
    const tags = ["Brand:Piscine Laghetto"];
    const rawTags = record.Tags ? record.Tags.split(",").map((t: string) => t.trim()) : [];
    
    rawTags.forEach(tag => {
        if (tag.toLowerCase().includes("fuori terra")) {
            tags.push("Categoria:Piscine fuori terra");
            tags.push("Sottocategoria:Piscine in acciaio"); // Default per Laghetto se acciaio
        } else if (tag.toLowerCase().includes("interrata")) {
            tags.push("Categoria:Piscine fuori terra"); // JollyGame mette interrate sotto fuori terra? Controlliamo le collezioni.
            tags.push("Sottocategoria:Piscine interrate");
        } else if (tag.toLowerCase().includes("filtro") || tag.toLowerCase().includes("filtraggio")) {
            tags.push("Categoria:Filtraggio");
        }
        tags.push(`OriginalTag:${tag}`);
    });

    const metafields = [];
    if (record.Titolo) {
      metafields.push({ namespace: "global", key: "title_tag", type: "string", value: `${title} | Piscine Laghetto` });
    }

    console.log(`\n🌊 [Laghetto: ${title}] Step 1: Creazione Prodotto...`);
    const productRes = await shopifyRequest(productCreateMutation, {
      input: { title, descriptionHtml, vendor: "Piscine Laghetto", tags, status: "DRAFT", metafields }
    });

    const productId = productRes.data?.productCreate?.product?.id;
    if (!productId) {
      console.error(`❌ Errore:`, productRes.data?.productCreate?.userErrors || productRes.errors);
      continue;
    }

    // 2. Variante (Prezzo 0 per Laghetto solitamente richiede preventivo)
    await shopifyRequest(productVariantCreateMutation, {
      input: { productId, price: "0.00", sku: `LAG-${record.URL.split("/").pop()}` }
    });

    // 3. Media (Immagini + YouTube)
    const media = [];
    if (record.Immagini) {
      record.Immagini.split(",").map((url: string) => ({
        alt: title, mediaContentType: "IMAGE", originalSource: url.trim()
      })).slice(0, 8).forEach(m => media.push(m));
    }
    if (record.Video_YouTube) {
      record.Video_YouTube.split(",").forEach((url: string) => {
        media.push({ alt: title, mediaContentType: "EXTERNAL_VIDEO", originalSource: url.trim() });
      });
    }
    
    if (media.length > 0) {
      console.log(`🖼️ [${title}] Step 2: Caricamento Media...`);
      await shopifyRequest(productCreateMediaMutation, { productId, media });
    }

    // 4. PDF (Metaobjects)
    if (record.PDF_Documenti) {
      console.log(`📄 [${title}] Step 3: Gestione PDF...`);
      const docIds = [];
      const pdfs = record.PDF_Documenti.split(",").map((p: string) => p.trim());
      
      for (const pdf of pdfs) {
        const [label, url] = pdf.includes("|") ? pdf.split("|") : ["Documento Laghetto", pdf];
        if (!url || !url.startsWith("http")) continue;
        
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

    console.log(`✅ [${title}] Importato.`);
    await new Promise(r => setTimeout(r, 1000));
  }
}

importLaghetto().catch(console.error);
