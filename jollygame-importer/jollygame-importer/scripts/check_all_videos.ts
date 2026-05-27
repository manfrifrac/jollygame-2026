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

async function checkAllVideos() {
  let hasNextPage = true;
  let cursor = null;
  let totalWithVideo = 0;

  console.log("--- Ricerca Globale Video nei Metafield ---");

  while (hasNextPage) {
    const query = `
    query($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          title
          video_url: metafield(namespace: "custom", key: "video_url") { value }
          video_youtube: metafield(namespace: "custom", key: "video_youtube") { value }
          youtube_videos: metafield(namespace: "custom", key: "youtube_videos") { value }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    const products = res.data?.products?.nodes || [];

    products.forEach((p: any) => {
      if (p.video_url || p.video_youtube || p.youtube_videos) {
        console.log(`✅ ${p.title}`);
        if (p.video_url) console.log(`   - custom.video_url: ${p.video_url.value}`);
        if (p.video_youtube) console.log(`   - custom.video_youtube: ${p.video_youtube.value}`);
        if (p.youtube_videos) console.log(`   - custom.youtube_videos: ${p.youtube_videos.value}`);
        totalWithVideo++;
      }
    });

    hasNextPage = res.data?.products?.pageInfo?.hasNextPage;
    cursor = res.data?.products?.pageInfo?.endCursor;
  }

  console.log(`\nFine ricerca. Prodotti con video trovati: ${totalWithVideo}`);
}

checkAllVideos().catch(console.error);
