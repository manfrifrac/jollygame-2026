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

async function forceReorganize() {
  console.log("🚀 Avvio riorganizzazione FORZATA Collezioni...");

  const colQuery = `{ collections(first: 250) { nodes { id title } } }`;
  const colRes = await shopifyRequest(colQuery);
  const collections = colRes.data.collections.nodes;
  const colMap: Record<string, string> = {};
  collections.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const noPriceId = colMap["no price"];

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getProducts($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes { id title vendor }
        }
      }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const title = product.title.toLowerCase();
        let targetColName = null;

        if (title.includes("iq") || title.includes("vortex") || title.includes("alpha") || title.includes("voyager") || title.includes("cnx") || title.includes("robot")) {
            targetColName = "pulitori elettrico";
        } else if (title.includes("pompa di calore") || title.includes("z250") || title.includes("z350") || title.includes("z400") || title.includes("z550")) {
            targetColName = "pompe di calore";
        } else if (title.includes("elettrolisi") || title.includes("sale") || title.includes("exo") || title.includes("ei2") || title.includes("eisalt")) {
            targetColName = "trattamento acqua";
        } else if (title.includes("piscina") && product.vendor === "Gre") {
            targetColName = "piscine in legno"; // Default per Gre se non specificato altro
        } else if (product.vendor === "Piscine Laghetto") {
            targetColName = "piscine fuori terra";
        }

        const targetColId = targetColName ? colMap[targetColName] : null;

        if (targetColId) {
            const mutation = `
              mutation productUpdate($input: ProductInput!) {
                productUpdate(input: $input) {
                  product { id }
                  userErrors { message }
                }
              }
            `;
            const input: any = { id: product.id, collectionsToJoin: [targetColId] };
            if (noPriceId) input.collectionsToLeave = [noPriceId];

            const updRes = await shopifyRequest(mutation, { input });
            if (updRes.data?.productUpdate?.product) {
                updatedCount++;
                process.stdout.write(".");
            }
        }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n\n✅ Riorganizzazione forzata completata! ${updatedCount} prodotti processati.`);
}

forceReorganize().catch(console.error);
