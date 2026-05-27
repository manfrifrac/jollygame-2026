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

async function checkMedia(vendor: string) {
  const query = `
  query($query: String!) {
    products(first: 20, query: $query) {
      nodes {
        title
        media(first: 10) {
          nodes {
            mediaContentType
            ... on ExternalVideo {
              originUrl
              embedUrl
            }
          }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query, { query: `vendor:'${vendor}'` });
  const products = res.data?.products?.nodes || [];
  
  console.log(`--- Ispezione Media Prodotti ${vendor} ---`);
  products.forEach((p: any) => {
    const videos = p.media.nodes.filter((m: any) => m.mediaContentType === "EXTERNAL_VIDEO");
    if (videos.length > 0) {
      console.log(`\n✅ ${p.title}`);
      videos.forEach((v: any) => {
        console.log(`   - Video: ${v.originUrl || v.embedUrl}`);
      });
    }
  });
}

async function main() {
    await checkMedia("Zodiac");
    await checkMedia("Piscine Laghetto");
}

main().catch(console.error);
