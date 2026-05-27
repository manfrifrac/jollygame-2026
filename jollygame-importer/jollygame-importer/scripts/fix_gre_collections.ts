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

async function fixGreCollections() {
  console.log("🛠️  Spostamento prodotti Gre in Collezioni Specifiche...");

  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const legnoId = colMap["piscine in legno"];
  const acciaioId = colMap["piscine in acciaio"];
  const fuoriTerraId = colMap["piscine fuori terra"];

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getGre($cursor: String) {
        products(first: 250, after: $cursor, query: "vendor:Gre") {
          pageInfo { hasNextPage endCursor }
          nodes {
            id title metafields(first: 20) { nodes { key value } }
            collections(first: 10) { nodes { id title } }
          }
        }
      }
    `;
    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const title = product.title.toLowerCase();
        const currentCats = product.collections.nodes.map((c: any) => c.title.toLowerCase());
        const materiale = product.metafields.nodes.find((m: any) => m.key === "materiale")?.value;
        
        let targetId = null;
        let targetName = null;

        if (materiale === "Legno" || title.includes("legno")) {
            targetId = legnoId; targetName = "piscine in legno";
        } else if (materiale === "Acciaio" || title.includes("acciaio") || title.includes("pacific") || title.includes("sicilia") || title.includes("anthracite")) {
            targetId = acciaioId; targetName = "piscine in acciaio";
        }

        if (targetId && !currentCats.includes(targetName!)) {
            console.log(`📦 Spostamento: ${product.title} -> [${targetName}]`);
            const input: any = { 
                id: product.id, 
                collectionsToJoin: [targetId],
                collectionsToLeave: [fuoriTerraId].filter(id => id && currentCats.includes("piscine fuori terra"))
            };
            await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, { input });
            updatedCount++;
        }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  console.log(`✅ Aggiornati ${updatedCount} prodotti Gre.`);
}

fixGreCollections().catch(console.error);
