import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function getProductsByVendor(vendor: string) {
  let hasNextPage = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNextPage) {
    const query = `
    query($cursor: String, $query: String!) {
      products(first: 250, after: $cursor, query: $query) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor, query: `vendor:'${vendor}'` });
    if (res.data?.products?.nodes) {
        products.push(...res.data.products.nodes);
    }
    hasNextPage = res.data?.products?.pageInfo?.hasNextPage;
    cursor = res.data?.products?.pageInfo?.endCursor;
  }
  return products;
}

async function updateProductMetafield(productId: string, videoUrl: string) {
  const mutation = `
  mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
      product { id }
      userErrors { message field }
    }
  }
  `;

  // We are storing it as a single line string based on the user's theme modification:
  // {%- assign video_url = product.metafields.custom.video_url -%}
  const res = await shopifyRequest(mutation, {
    input: {
      id: productId,
      metafields: [
        {
          namespace: "custom",
          key: "video_url",
          value: videoUrl,
          type: "single_line_text_field" // or url if defined as URL type
        }
      ]
    }
  });

  if (res.data?.productUpdate?.userErrors?.length > 0) {
      // If it fails, try as URL type just in case the definition forces it
      const fallbackRes = await shopifyRequest(mutation, {
        input: {
          id: productId,
          metafields: [
            {
              namespace: "custom",
              key: "video_url",
              value: videoUrl,
              type: "url"
            }
          ]
        }
      });
      if (fallbackRes.data?.productUpdate?.userErrors?.length > 0) {
          console.error(`❌ Errore aggiornamento ${productId}:`, fallbackRes.data.productUpdate.userErrors[0].message);
          return false;
      }
  }
  return true;
}

async function uploadVideos() {
  console.log("🚀 Inizio caricamento URL Video nei Metafield...");

  // 1. Leggi Zodiac CSV
  const zodiacCsv = path.resolve("../../zodiac_enriched_data.csv");
  let zodiacRecords: any[] = [];
  if (fs.existsSync(zodiacCsv)) {
    zodiacRecords = parse(fs.readFileSync(zodiacCsv, "utf-8"), { columns: true, skip_empty_lines: true });
  }

  // 2. Leggi Laghetto CSV
  const laghettoCsv = path.resolve("../../laghetto_full_export_enriched.csv");
  let laghettoRecords: any[] = [];
  if (fs.existsSync(laghettoCsv)) {
    laghettoRecords = parse(fs.readFileSync(laghettoCsv, "utf-8"), { columns: true, skip_empty_lines: true });
  }

  console.log(`Caricati ${zodiacRecords.length} record Zodiac e ${laghettoRecords.length} record Laghetto.`);

  const zodiacProducts = await getProductsByVendor("Zodiac");
  const laghettoProducts = await getProductsByVendor("Piscine Laghetto");
  
  const allShopifyProducts = [...zodiacProducts, ...laghettoProducts];
  console.log(`Trovati ${allShopifyProducts.length} prodotti in Shopify.`);

  let updatedCount = 0;

  for (const shopifyProd of allShopifyProducts) {
    let videoUrl = "";

    // Cerca in Zodiac
    const zMatch = zodiacRecords.find(r => r.Titolo.trim().toLowerCase() === shopifyProd.title.trim().toLowerCase());
    if (zMatch && zMatch.YouTube_Videos) {
        // Estrai il primo link YouTube vero (ignorando immagini placeholder)
        const links = zMatch.YouTube_Videos.split(";");
        const realVideo = links.find((l: string) => l.includes("youtube.com/embed") || l.includes("watch?v=") || l.includes("youtu.be"));
        if (realVideo) videoUrl = realVideo.trim();
    }

    // Cerca in Laghetto se non trovato in Zodiac
    if (!videoUrl) {
        const lMatch = laghettoRecords.find(r => r.Titolo.trim().toLowerCase() === shopifyProd.title.trim().toLowerCase());
        if (lMatch && lMatch.Video_YouTube) {
            const links = lMatch.Video_YouTube.split(";");
            const realVideo = links.find((l: string) => l.includes("youtube.com") || l.includes("youtu.be"));
            if (realVideo) videoUrl = realVideo.trim();
        }
    }

    if (videoUrl) {
        console.log(`📹 Aggiungo video per [${shopifyProd.title}]: ${videoUrl}`);
        const success = await updateProductMetafield(shopifyProd.id, videoUrl);
        if (success) updatedCount++;
        await new Promise(r => setTimeout(r, 600)); // Rate limiting
    }
  }

  console.log(`\n✅ Operazione completata. Video aggiunti a ${updatedCount} prodotti.`);
}

uploadVideos().catch(console.error);
