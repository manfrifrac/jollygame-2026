import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

// agreed filters
const SPARE_KEYWORDS = ['vite', 'bullone', 'guarnizione', 'tappo', 'raccordo', 'valvola', 'tubo', 'perno', 'molla', 'adattatore', 'connettore', 'staffa', 'supporto', 'piastra', 'vano skimmer'];
const LEISURE_KEYWORDS = ['cuffia', 'occhialini', 'maschera', 'boccaglio', 'snorkeling', 'pallone', 'gioco', 'beach ball', 'canestro', 'porta da calcio', 'giubbino salvataggio'];
const BABY_POOL_KEYWORDS = ['mini frame', 'small frame', 'piscina bambini', 'piscina baby', 'tre anelli', 'quattro anelli'];

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

const PRODUCT_VARIANTS_BULK_CREATE = `
mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!, $strategy: ProductVariantsBulkCreateStrategy) {
  productVariantsBulkCreate(productId: $productId, variants: $variants, strategy: $strategy) {
    product { id }
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

async function runDefinitiveImport() {
  const csvPath = path.resolve("../../gold_consolidated_final.csv");
  const content = fs.readFileSync(csvPath, "utf-8");
  const records = parse(content, { columns: true, skip_empty_lines: true });

  // Filter and Group
  const masterGroups: Record<string, any[]> = {};
  for (const record of records) {
    const title = record.Titolo.toLowerCase();
    const price = float(record.Prezzo);
    
    let exclude = false;
    if (any(SPARE_KEYWORDS, title)) exclude = true;
    else if (any(LEISURE_KEYWORDS, title)) exclude = true;
    else if (any(BABY_POOL_KEYWORDS, title) && price < 100) exclude = true;
    else if (price < 25 && !record.Titolo.toLowerCase().includes('cartucc')) exclude = true;

    if (!exclude) {
      if (!masterGroups[record.Master_Title]) masterGroups[record.Master_Title] = [];
      masterGroups[record.Master_Title].push(record);
    }
  }

  const masterTitles = Object.keys(masterGroups);
  console.log(`🚀 Avvio Importazione Definitiva: ${masterTitles.length} Prodotti Master.`);

  // Skip the two test products if they already exist
  const skipList = ["Piscina Power Steel Rettangolare", "Piscina Power Steel Rotonda"];

  for (const masterTitle of masterTitles) {
    if (skipList.includes(masterTitle)) {
        console.log(`⏭️ Skipping test product: ${masterTitle}`);
        continue;
    }

    const variants = masterGroups[masterTitle];
    console.log(`📦 Import: ${masterTitle} (${variants.length} varianti)`);

    // 1. Create Master Product
    const prodRes = await shopifyRequest(PRODUCT_CREATE, {
      input: {
        title: masterTitle,
        descriptionHtml: variants[0].Descrizione_HTML,
        vendor: variants[0].Tags.includes('Intex') ? 'Intex' : 'Bestway',
        tags: variants[0].Tags.split(','),
        status: "ACTIVE", // LIVE!
        productOptions: [{
            name: "Modello/Misura",
            values: Array.from(new Set(variants.map(v => v.Variant_Detail || v.SKU))).map(val => ({ name: val }))
        }]
      }
    });

    const productId = prodRes.data?.productCreate?.product?.id;
    if (!productId) {
      console.error(`❌ Error Create ${masterTitle}:`, prodRes.data?.productCreate?.userErrors || prodRes.errors);
      continue;
    }

    // 2. Add Variants in Bulk
    const variantInputs = variants.map(v => ({
        price: v.Prezzo.replace(',', '.'),
        inventoryItem: { sku: v.SKU },
        barcode: (v.EAN && v.EAN !== 'None') ? v.EAN : null,
        optionValues: [{ optionName: "Modello/Misura", name: v.Variant_Detail || v.SKU }]
    }));

    await shopifyRequest(PRODUCT_VARIANTS_BULK_CREATE, {
        productId,
        variants: variantInputs,
        strategy: "REMOVE_STANDALONE_VARIANT"
    });

    // 3. Media (from first variant)
    const images = JSON.parse(variants[0].Immagini_JSON || "[]");
    if (images.length > 0) {
        const mediaInput = images.slice(0, 5).map((url: string) => ({
            alt: masterTitle,
            mediaContentType: "IMAGE",
            originalSource: url
        }));
        await shopifyRequest(PRODUCT_CREATE_MEDIA, { productId, media: mediaInput });
    }
    
    console.log(`✅ Success: https://${SHOP_DOMAIN}/products/${prodRes.data.productCreate.product.handle}`);
    
    // Safety delay
    await new Promise(r => setTimeout(r, 1200));
  }
}

function any(keywords: string[], text: string) {
    return keywords.some(k => text.includes(k));
}
function float(val: string) {
    try { return parseFloat(val.replace(',','.')); } catch { return 0; }
}

runDefinitiveImport().catch(console.error);
