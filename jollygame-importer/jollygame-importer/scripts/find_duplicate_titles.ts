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

async function findDuplicateTitles() {
  console.log("🔍 Identificazione titoli duplicati nel catalogo...");

  let hasNextPage = true;
  let cursor = null;
  const titleMap: Record<string, string[]> = {};

  while (hasNextPage) {
    const query = `
    query getTitles($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const normalizedTitle = product.title.toLowerCase().trim();
        if (!titleMap[normalizedTitle]) titleMap[normalizedTitle] = [];
        titleMap[normalizedTitle].push(product.id);
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const duplicates = Object.entries(titleMap).filter(([title, ids]) => ids.length > 1);
  
  console.log(`\n⚠️ Trovati ${duplicates.length} titoli con duplicati:`);
  duplicates.forEach(([title, ids]) => {
    console.log(`- "${title}": ${ids.length} istanze (${ids.join(", ")})`);
  });
}

findDuplicateTitles().catch(console.error);
