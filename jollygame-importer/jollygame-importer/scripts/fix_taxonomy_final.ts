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

async function fixTaxonomyFinal() {
  console.log("🛠️  Fix finale tassonomia: FORMA e CATEGORIA...");

  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  let cursor = null;
  let hasNextPage = true;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getProducts($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id title vendor
            metafields(first: 20) { nodes { key value } }
            collections(first: 10) { nodes { title } }
          }
        }
      }
    `;
    const res = await shopifyRequest(query, { cursor });
    const products = res.data.products.nodes;

    for (const product of products) {
      const title = product.title.toLowerCase();
      const metaUpdates: any[] = [];
      const collectionsToJoin: string[] = [];
      const currentCats = product.collections.nodes.map((c: any) => c.title.toLowerCase());

      // 1. FORMA (Rilevazione dal titolo)
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
              console.log(`✨ Forma [${detectedShape}] -> ${product.title}`);
          }
      }

      // 2. CATEGORIZZAZIONE (Spostamento da 'no price' o collezioni errate)
      let targetColName = null;
      if (title.includes("ra ") || title.includes("oa ") || title.includes("swy") || title.includes("robot") || title.includes("pulitore elettrico")) {
          targetColName = "pulitori elettrico";
      } else if (title.includes("z250") || title.includes("z350") || title.includes("z400") || title.includes("z550") || title.includes("sirocco") || title.includes("heat line")) {
          targetColName = "pompe di calore";
      } else if (product.vendor === "Piscine Laghetto") {
          targetColName = "piscine fuori terra";
      } else if (product.vendor === "Gre" && (title.includes("piscina") || title.includes("ovale") || title.includes("rotonda") || title.includes("rettangolare"))) {
          targetColName = "piscine in legno"; // Collezione principale Gre
      }

      if (targetColName && colMap[targetColName] && !currentCats.includes(targetColName)) {
          collectionsToJoin.push(colMap[targetColName]);
          console.log(`📦 Categoria [${targetColName}] -> ${product.title}`);
      }

      if (metaUpdates.length > 0 || collectionsToJoin.length > 0) {
          const input: any = { id: product.id };
          if (metaUpdates.length > 0) input.metafields = metaUpdates;
          if (collectionsToJoin.length > 0) {
              input.collectionsToJoin = collectionsToJoin;
              if (currentCats.includes("no price")) {
                  input.collectionsToLeave = [colMap["no price"]];
              }
          }
          await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, { input });
          updatedCount++;
      }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  console.log(`✅ Operazione conclusa. Aggiornati ${updatedCount} prodotti.`);
}

fixTaxonomyFinal().catch(console.error);
