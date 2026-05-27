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

async function searchShopifyHTML() {
  let hasNextPage = true;
  let cursor = null;
  let foundProducts = 0;

  console.log("🔍 Ricerca video/iframe/QR nelle descrizioni Shopify...");

  while (hasNextPage) {
    const query = `
    query($cursor: String) {
      products(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          title
          descriptionHtml
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    const products = res.data?.products?.nodes || [];

    for (const p of products) {
        if (!p.descriptionHtml) continue;
        const html = p.descriptionHtml.toLowerCase();
        if (html.includes("youtube") || html.includes("vimeo") || html.includes("iframe") || html.includes("qr") || html.includes("video")) {
            console.log(`\n✅ Prodotto trovato: ${p.title}`);
            if (html.includes("youtube")) console.log("   - Trovato: youtube");
            if (html.includes("vimeo")) console.log("   - Trovato: vimeo");
            if (html.includes("iframe")) console.log("   - Trovato: iframe");
            if (html.includes("qr")) {
                // simple regex to extract context around qr
                const match = p.descriptionHtml.match(/.{0,30}qr.{0,30}/i);
                console.log(`   - Trovato 'qr': "${match ? match[0] : ''}"`);
            }
            if (html.includes("video")) {
                const match = p.descriptionHtml.match(/.{0,30}video.{0,30}/i);
                console.log(`   - Trovato 'video': "${match ? match[0] : ''}"`);
            }
            foundProducts++;
        }
    }

    hasNextPage = res.data?.products?.pageInfo?.hasNextPage;
    cursor = res.data?.products?.pageInfo?.endCursor;
  }
  
  console.log(`\nTotale prodotti con match: ${foundProducts}`);
}

searchShopifyHTML().catch(console.error);
