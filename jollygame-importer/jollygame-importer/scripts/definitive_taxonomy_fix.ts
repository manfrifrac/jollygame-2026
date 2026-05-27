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

async function definitiveTaxonomyFix() {
  console.log("🛠️  Avvio Fix Tassonomia Definitivo (Forme e Categorie)...");

  // 1. Recupero Collezioni Target
  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const noPriceId = colMap["no price"];
  const robotId = colMap["pulitori elettrico"];
  const legnoId = colMap["piscine in legno"];
  const laghettoId = colMap["piscine fuori terra"];
  const hPId = colMap["pompe di calore"];

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getProducts($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            title
            vendor
            metafields(first: 20) { nodes { key value } }
          }
        }
      }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const title = product.title.toLowerCase();
      const metaUpdates: any[] = [];
      const collectionsToJoin: string[] = [];

      // A. FIX FORMA (Metafield)
      const currentShape = product.metafields.nodes.find((m: any) => m.key === "forma")?.value;
      if (!currentShape || currentShape === "Non definito" || currentShape === "MISSING") {
          let detectedShape = null;
          if (title.includes("ovale")) detectedShape = "Ovale";
          else if (title.includes("rotonda") || title.includes("tonda")) detectedShape = "Rotonda";
          else if (title.includes("rettangolare")) detectedShape = "Rettangolare";
          else if (title.includes("quadrata")) detectedShape = "Quadrata";
          else if (title.includes("otto")) detectedShape = "Forma di otto";

          if (detectedShape) {
              metaUpdates.push({ namespace: "custom", key: "forma", value: detectedShape, type: "single_line_text_field" });
          }
      }

      // B. FIX CATEGORIA (Collezione)
      if (title.includes("ra ") || title.includes("oa ") || title.includes("swy") || title.includes("robot")) {
          if (robotId) collectionsToJoin.push(robotId);
      } else if (title.includes("z250") || title.includes("z350") || title.includes("z400") || title.includes("z550") || title.includes("z650")) {
          if (hPId) collectionsToJoin.push(hPId);
      } else if (product.vendor === "Piscine Laghetto") {
          if (laghettoId) collectionsToJoin.push(laghettoId);
      } else if (product.vendor === "Gre" && (title.includes("piscina") || title.includes("ovale") || title.includes("rotonda"))) {
          if (legnoId) collectionsToJoin.push(legnoId);
      }

      if (metaUpdates.length > 0 || collectionsToJoin.length > 0) {
          const input: any = { id: product.id };
          if (metaUpdates.length > 0) input.metafields = metaUpdates;
          if (collectionsToJoin.length > 0) {
              input.collectionsToJoin = collectionsToJoin;
              if (noPriceId) input.collectionsToLeave = [noPriceId];
          }

          const updRes = await shopifyRequest(`mutation productUpdate($input: ProductInput!) { productUpdate(input: $input) { product { id } userErrors { message } } }`, { input });
          if (updRes.data?.productUpdate?.product) {
              updatedCount++;
              process.stdout.write(".");
          }
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n\n✅ Tassonomia e Categorie aggiornate per ${updatedCount} prodotti.`);
}

definitiveTaxonomyFix().catch(console.error);
