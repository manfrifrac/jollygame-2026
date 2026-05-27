import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function disableNoImageProducts() {
  console.log("🔍 Identificazione prodotti senza immagini per disattivazione...");
  
  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        mediaCount { count }
        status
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    products.push(...res.data.products.nodes);
    hasNext = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const toDisable = products.filter(p => p.mediaCount.count === 0 && p.status === 'ACTIVE');

  if (toDisable.length === 0) {
      console.log("✨ Non ci sono prodotti attivi senza immagini.");
      return;
  }

  console.log(`\n🚫 Disattivazione di ${toDisable.length} prodotti...`);
  
  for (const p of toDisable) {
    const mutation = `
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id status }
        userErrors { message }
      }
    }
    `;

    await shopifyRequest(mutation, {
      input: {
        id: p.id,
        status: "DRAFT"
      }
    });
    console.log(`  💤 Messo in bozza: ${p.title}`);
  }

  console.log("\n✅ Operazione completata.");
}

disableNoImageProducts().catch(console.error);
