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

async function taxonomyNuclearFixV2() {
  console.log("☢️  Avvio Fix Tassonomia NUCLEARE V2 (Smart Matching)...");

  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getProducts($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id title vendor
            metafields(first: 20) { nodes { key value } }
            collections(first: 20) { nodes { id title } }
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
      const collectionsToLeave: string[] = [];
      const currentCats = product.collections.nodes.map((c: any) => c.title.toLowerCase());

      // 1. FIX FORMA (Sempre attivo)
      const currentShape = product.metafields.nodes.find((m: any) => m.key === "forma")?.value;
      if (!currentShape || currentShape === "Non definito" || currentShape === "MISSING") {
          let detectedShape = null;
          if (title.includes("ovale")) detectedShape = "Ovale";
          else if (title.includes("rotonda") || title.includes("tonda")) detectedShape = "Rotonda";
          else if (title.includes("rettangolare")) detectedShape = "Rettangolare";
          else if (title.includes("quadrata")) detectedShape = "Quadrata";
          else if (title.includes("otto")) detectedShape = "Forma di otto";
          if (detectedShape) metaUpdates.push({ namespace: "custom", key: "forma", value: detectedShape, type: "single_line_text_field" });
      }

      // 2. LOGICA CATEGORIE (Rigida)
      let targetCatName = null;
      if (title.includes("ra ") || title.includes("oa ") || title.includes("swy") || title.includes("robot") || title.includes("pulitore elettrico")) {
          targetCatName = "pulitori elettrico";
      } else if (title.includes("z250") || title.includes("z350") || title.includes("z400") || title.includes("z550") || title.includes("sirocco") || title.includes("heat line")) {
          targetCatName = "pompe di calore";
      } else if (product.vendor === "Piscine Laghetto") {
          targetCatName = "piscine fuori terra";
      } else if (product.vendor === "Gre" && (title.includes("piscina") || title.includes("ovale") || title.includes("rotonda") || title.includes("rettangolare"))) {
          const materiale = product.metafields.nodes.find((m: any) => m.key === "materiale")?.value;
          if (materiale === "Acciaio" || title.includes("acciaio") || title.includes("pacific") || title.includes("sicilia") || title.includes("anthracite")) {
              targetCatName = "piscine in acciaio";
          } else if (materiale === "Legno" || title.includes("legno")) {
              targetCatName = "piscine in legno";
          }
      }

      if (targetCatName && colMap[targetCatName] && !currentCats.includes(targetCatName)) {
          collectionsToJoin.push(colMap[targetCatName]);
          // Pulizia categorie vecchie/generiche
          if (currentCats.includes("no price") && colMap["no price"]) collectionsToLeave.push(colMap["no price"]);
          if (currentCats.includes("piscine fuori terra") && targetCatName !== "piscine fuori terra" && colMap["piscine fuori terra"]) {
              collectionsToLeave.push(colMap["piscine fuori terra"]);
          }
      }

      if (metaUpdates.length > 0 || collectionsToJoin.length > 0) {
          console.log(`🚀 Update: ${product.title}`);
          const input: any = { id: product.id };
          if (metaUpdates.length > 0) input.metafields = metaUpdates;
          if (collectionsToJoin.length > 0) input.collectionsToJoin = collectionsToJoin;
          if (collectionsToLeave.length > 0) input.collectionsToLeave = collectionsToLeave;

          await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, { input });
          updatedCount++;
          process.stdout.write(".");
      }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  console.log(`\n\n✅ Fix Nucleare V2 completato per ${updatedCount} prodotti.`);
}

taxonomyNuclearFixV2().catch(console.error);
