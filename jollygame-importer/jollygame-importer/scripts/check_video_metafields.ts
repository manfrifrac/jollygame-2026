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

async function checkVideos() {
  const query = `
  {
    products(first: 50) {
      nodes {
        title
        video_url: metafield(namespace: "custom", key: "video_url") { value }
        video_youtube: metafield(namespace: "custom", key: "video_youtube") { value }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];
  
  console.log("--- Report Video Prodotti ---");
  let found = 0;
  products.forEach((p: any) => {
    if (p.video_url || p.video_youtube) {
      console.log(`✅ ${p.title}`);
      if (p.video_url) console.log(`   - custom.video_url: ${p.video_url.value}`);
      if (p.video_youtube) console.log(`   - custom.video_youtube: ${p.video_youtube.value}`);
      found++;
    }
  });

  if (found === 0) {
    console.log("❌ Nessun video trovato nei metafields dei primi 50 prodotti.");
  } else {
    console.log(`\nTotale prodotti con video trovati: ${found}`);
  }
}

checkVideos().catch(console.error);
