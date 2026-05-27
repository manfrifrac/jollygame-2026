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

async function taxonomyCleanupFinalV8() {
  console.log("🧹 Pulizia Tassonomia V8 (Spostamento Massivo e Pulizia 'no price')...");

  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

  const noPriceId = colMap["no price"];
  const linerId = colMap["liner e riparatori"];
  const accessoriId = colMap["altri accessori"];
  const materialePuliziaId = colMap["materiale di pulizia"];
  const analisiId = colMap["analisi dell'acqua"];
  const chimicaId = colMap["prodotti chimici"];
  const filtriId = colMap["filtri"];
  const pompeId = colMap["pompe per piscine"];

  let hasNextPage = true;
  let cursor = null;
  let updatedCount = 0;

  while (hasNextPage) {
    const query = `
      query getProds($cursor: String) {
        products(first: 50, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id title vendor collections(first: 20) { nodes { id title } }
          }
        }
      }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;
    const products = res.data.products.nodes;

    for (const product of products) {
      const title = product.title.toLowerCase();
      const currentIds = product.collections.nodes.map((c: any) => c.id);
      const currentTitles = product.collections.nodes.map((c: any) => c.title.toLowerCase());
      
      const join = [];
      const leave = [];

      // Determiniamo la categoria target basata su parole chiave
      let targetId = null;
      if (title.includes("liner")) targetId = linerId;
      else if (title.includes("raccordo") || title.includes("tubo") || title.includes("valvola") || title.includes("tappo") || title.includes("skimmer")) targetId = accessoriId;
      else if (title.includes("spazzola") || title.includes("manico") || title.includes("retino") || title.includes("termometro")) targetId = materialePuliziaId;
      else if (title.includes("batteria") || title.includes("sonda") || title.includes("blue connect") || title.includes("tester")) targetId = analisiId;
      else if (title.includes("cloro") || title.includes("bromo") || title.includes("ossigeno") || title.includes("adesivo") || title.includes("flocculante")) targetId = chimicaId;
      else if (title.includes("filtro") || title.includes("depuratore") || title.includes("cartuccia")) targetId = filtriId;
      else if (title.includes("pompa") || title.includes("flopro")) targetId = pompeId;

      if (targetId && !currentIds.includes(targetId)) join.push(targetId);

      // Pulizia categorie errate/generiche per i ricambi/accessori
      if (targetId || title.includes("robot") || title.includes("pompa di calore")) {
          // Se ha un prezzo o una categoria specifica, deve lasciare 'no price'
          if (currentTitles.includes("no price") && noPriceId) leave.push(noPriceId);
          // Se è un ricambio/accessorio, deve lasciare le categorie 'Piscine'
          if (targetId && targetId !== linerId) {
              ["piscine fuori terra", "piscine in legno", "piscine in acciaio"].forEach(cat => {
                  if (currentTitles.includes(cat) && colMap[cat]) leave.push(colMap[cat]);
              });
          }
      }

      if (join.length > 0 || leave.length > 0) {
          console.log(`🚀 Fix: ${product.title}`);
          const updRes = await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } userErrors { message } } }`, {
              input: { id: product.id, collectionsToJoin: join, collectionsToLeave: leave }
          });
          if (updRes.data?.productUpdate?.product) {
              updatedCount++;
              process.stdout.write(".");
          } else {
              console.error(`\n❌ Error:`, JSON.stringify(updRes.data?.productUpdate?.userErrors));
          }
          await new Promise(r => setTimeout(r, 200));
      }
    }
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }
  console.log(`\n\n✅ Concluso per ${updatedCount} prodotti.`);
}

taxonomyCleanupFinalV8().catch(console.error);
