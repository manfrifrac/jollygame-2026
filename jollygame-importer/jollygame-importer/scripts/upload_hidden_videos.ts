import fs from "fs";
import path from "path";
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

  // We are storing it as a single line string
  const res = await shopifyRequest(mutation, {
    input: {
      id: productId,
      metafields: [
        {
          namespace: "custom",
          key: "video_url",
          value: videoUrl,
          type: "single_line_text_field"
        }
      ]
    }
  });

  if (res.data?.productUpdate?.userErrors?.length > 0) {
      console.error(`❌ Errore aggiornamento ${productId}:`, res.data.productUpdate.userErrors[0].message);
      return false;
  }
  return true;
}

async function uploadVideos() {
  console.log("🚀 Inizio caricamento URL Video (Hidden Zodiac) nei Metafield...");

  const jsonPath = path.resolve("../../zodiac_hidden_videos.json");
  if (!fs.existsSync(jsonPath)) {
      console.error("❌ json file not found:", jsonPath);
      return;
  }
  const videoMap = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));
  console.log(`Caricati ${Object.keys(videoMap).length} video mappati.`);

  const zodiacProducts = await getProductsByVendor("Zodiac");
  console.log(`Trovati ${zodiacProducts.length} prodotti Zodiac in Shopify.`);

  let updatedCount = 0;

  for (const shopifyProd of zodiacProducts) {
    // Find the matching video by title
    const videoUrl = videoMap[shopifyProd.title.trim()];

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
