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

async function findDuplicates() {
  console.log("🔍 Ricerca duplicati approfondita...");
  
  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        handle
        vendor
        variants(first: 1) {
          nodes {
            sku
            price
          }
        }
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

  const nameMap: Record<string, any[]> = {};
  const skuMap: Record<string, any[]> = {};

  products.forEach(p => {
    const name = p.title.toLowerCase().trim();
    const sku = p.variants.nodes[0]?.sku || "NO-SKU";

    if (!nameMap[name]) nameMap[name] = [];
    nameMap[name].push(p);

    if (sku !== "NO-SKU") {
        if (!skuMap[sku]) skuMap[sku] = [];
        skuMap[sku].push(p);
    }
  });

  console.log("\n👯 PRODOTTI DUPLICATI TROVATI:");
  let totalDuplicates = 0;

  for (const name in nameMap) {
    if (nameMap[name].length > 1) {
      totalDuplicates++;
      console.log(`\n📛 Nome: "${nameMap[name][0].title}" (${nameMap[name].length} istanze)`);
      nameMap[name].forEach(p => {
        console.log(`   - ID: ${p.id} | SKU: ${p.variants.nodes[0]?.sku} | Prezzo: ${p.variants.nodes[0]?.price}`);
      });
    }
  }

  if (totalDuplicates === 0) console.log("✨ Nessun duplicato per nome trovato.");
}

findDuplicates().catch(console.error);
