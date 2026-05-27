import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function fixLinersDefinitive() {
  console.log("🛠️  Spostamento Liner nella collezione corretta...");

  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const linerId = colMap["liner e riparatori"];
  const interrateId = colMap["piscine interrate"];
  const legnoId = colMap["piscine in legno"];
  const acciaioId = colMap["piscine in acciaio"];
  const fuoriTerraId = colMap["piscine fuori terra"];

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getLiners($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id title collections(first: 10) { id title }
          }
        }
      }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const title = product.title.toLowerCase();
        if (title.includes("liner")) {
            console.log(`📦 Analisi Liner: ${product.title}`);
            const currentIds = product.collections.nodes.map((c: any) => c.id);
            const leaveIds = [interrateId, legnoId, acciaioId, fuoriTerraId].filter(id => id && currentIds.includes(id));

            if (linerId && !currentIds.includes(linerId)) {
                const input: any = { 
                    id: product.id, 
                    collectionsToJoin: [linerId]
                };
                if (leaveIds.length > 0) input.collectionsToLeave = leaveIds;

                const updRes = await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, { input });
                if (updRes.data?.productUpdate?.product) {
                    updatedCount++;
                    console.log("   ✅ Spostato.");
                }
            } else {
                console.log("   ℹ️ Già OK.");
            }
        }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  console.log(`\n\n✅ Concluso: ${updatedCount} Liner sistemati.`);
}

fixLinersDefinitive().catch(console.error);
