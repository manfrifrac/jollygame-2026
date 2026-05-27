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

async function taxonomyNuclearFix() {
  console.log("☢️  Avvio Fix Tassonomia NUCLEARE (Update Metafields + Collections)...");

  // 1. Mappa Collezioni
  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const noPriceId = colMap["no price"];
  const robotId = colMap["pulitori elettrico"];
  const legnoId = colMap["piscine in legno"];
  const laghettoId = colMap["piscine fuori terra"];
  const hPId = colMap["pompe di calore"];
  const trattamentoId = colMap["trattamento acqua"];

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
            collections(first: 10) { nodes { id title } }
          }
        }
      }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const title = product.title.toLowerCase();
      const metaUpdates: any[] = [];
      let targetColId = null;
      let targetColName = null;

      // A. LOGICA FORMA
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

      // B. LOGICA CATEGORIA
      if (title.includes("ra ") || title.includes("oa ") || title.includes("swy") || title.includes("robot") || title.includes("pulitore")) {
          targetColId = robotId; targetColName = "pulitori elettrico";
      } else if (title.includes("z250") || title.includes("z350") || title.includes("z400") || title.includes("z550") || title.includes("sirocco") || title.includes("heat line")) {
          targetColId = hPId; targetColName = "pompe di calore";
      } else if (product.vendor === "Piscine Laghetto") {
          targetColId = laghettoId; targetColName = "piscine fuori terra";
      } else if (product.vendor === "Gre" && (title.includes("piscina") || title.includes("ovale") || title.includes("rotonda") || title.includes("rettangolare"))) {
          targetColId = legnoId; targetColName = "piscine in legno";
      } else if (title.includes("ei2") || title.includes("exo") || title.includes("sale") || title.includes("eisalt")) {
          targetColId = trattamentoId; targetColName = "trattamento acqua";
      }

      const currentColIds = product.collections.nodes.map((c: any) => c.id);
      const currentColTitles = product.collections.nodes.map((c: any) => c.title.toLowerCase());
      
      const needsColUpdate = targetColId && !currentColIds.includes(targetColId);

      if (metaUpdates.length > 0 || needsColUpdate) {
          console.log(`🚀 Aggiornamento: ${product.title}`);
          const input: any = { id: product.id };
          if (metaUpdates.length > 0) {
              input.metafields = metaUpdates;
              console.log(`   ✨ Meta: ${metaUpdates.map(m=>m.value).join(', ')}`);
          }
          if (needsColUpdate) {
              input.collectionsToJoin = [targetColId];
              if (currentColTitles.includes("no price")) {
                  input.collectionsToLeave = [noPriceId];
                  console.log(`   📦 Cat: [${targetColName}] (Lascio 'no price')`);
              } else {
                  console.log(`   📦 Cat: [${targetColName}]`);
              }
          }

          const updMutation = `mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } userErrors { message } } }`;
          const updRes = await shopifyRequest(updMutation, { input });
          
          if (updRes.data?.productUpdate?.product) {
              updatedCount++;
          } else {
              console.error(`   ❌ ERRORE:`, JSON.stringify(updRes.data?.productUpdate?.userErrors));
          }
          await new Promise(r => setTimeout(r, 200));
      }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  console.log(`\n\n✅ Fix Nucleare completato per ${updatedCount} prodotti.`);
}

taxonomyNuclearFix().catch(console.error);
