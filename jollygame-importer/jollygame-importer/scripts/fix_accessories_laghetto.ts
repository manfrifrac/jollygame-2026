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

async function fixAccessoriesAndLaghetto() {
  console.log("🛠️  Spostamento Accessori e Fix Forme Laghetto...");

  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const accessoriId = colMap["altri accessori"];
  const interrateId = colMap["piscine interrate"];

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getProds($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id title vendor collections(first: 10) { title }
          }
        }
      }
    `;
    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;
    const products = res.data.products.nodes;

    for (const product of products) {
      const title = product.title.toLowerCase();
      const metaUpdates: any[] = [];
      const collectionsToJoin: string[] = [];

      // 1. Identificazione Accessori
      if (product.vendor === "Gre") {
          if (title.includes("scalett") || title.includes("aspiratore") || title.includes("kit di pulizia") || title.includes("illuminazione") || title.includes("liner") || title.includes("copertura") || title.includes("tappeto") || title.includes("proiettore")) {
              if (accessoriId && !product.collections.nodes.some((c:any) => c.title.toLowerCase() === "altri accessori")) {
                  collectionsToJoin.push(accessoriId);
                  console.log(`📦 Move to Accessori: ${product.title}`);
              }
          }
      }

      // 2. Fix Forme Laghetto
      if (product.vendor === "Piscine Laghetto") {
          let shape = null;
          if (title.includes("city")) shape = "Quadrata";
          else if (title.includes("playa") || title.includes("dolcevita") || title.includes("bluespring") || title.includes("divina") || title.includes("classic")) shape = "Rettangolare";
          else if (title.includes("ninfea") || title.includes("pop")) shape = "Ovale";

          if (shape) {
              metaUpdates.push({ namespace: "custom", key: "forma", value: shape, type: "single_line_text_field" });
              console.log(`✨ Shape Laghetto [${shape}] -> ${product.title}`);
          }
          if (title.includes("bluespring") && interrateId) collectionsToJoin.push(interrateId);
      }

      if (metaUpdates.length > 0 || collectionsToJoin.length > 0) {
          const input: any = { id: product.id };
          if (metaUpdates.length > 0) input.metafields = metaUpdates;
          if (collectionsToJoin.length > 0) input.collectionsToJoin = collectionsToJoin;

          await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, { input });
          updatedCount++;
      }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  console.log(`✅ Operazione conclusa per ${updatedCount} prodotti.`);
}

fixAccessoriesAndLaghetto().catch(console.error);
