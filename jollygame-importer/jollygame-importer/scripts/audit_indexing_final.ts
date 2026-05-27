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

async function auditIndexing() {
  console.log("🔍 Avvio Audit Finale Indicizzazione e Accessori...");

  let hasNextPage = true;
  let cursor = null;
  const issues: any[] = [];

  while (hasNextPage) {
    const query = `
      query getProducts($cursor: String) {
        products(first: 250, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            title
            vendor
            handle
            collections(first: 10) {
              nodes {
                title
              }
            }
          }
        }
      }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const collections = product.collections.nodes.map((c: any) => c.title.toLowerCase());
      const title = product.title.toLowerCase();

      // Identifichiamo problemi di indicizzazione/categorizzazione
      let issueType = null;

      if (collections.length === 0) {
        issueType = "Nessuna Collezione";
      } else if (collections.includes("no price")) {
        issueType = "Ancora in 'no price'";
      } else if (collections.length === 1 && collections.includes("tutti i ricambi")) {
        issueType = "Solo in 'Tutti i Ricambi' (troppo generico)";
      }

      // Check specifici per accessori
      const isAccessorio = title.includes("raccordo") || title.includes("tubo") || title.includes("valvola") || 
                           title.includes("tappo") || title.includes("skimmer") || title.includes("guarnizione") ||
                           title.includes("spazzola") || title.includes("termometro") || title.includes("kit") ||
                           title.includes("batteria") || title.includes("sonda");

      if (isAccessorio && (collections.includes("piscine fuori terra") || collections.includes("piscine in legno") || collections.includes("piscine in acciaio"))) {
        issueType = "Accessorio mescolato con Piscine";
      }

      if (issueType) {
        issues.push({
          id: product.id,
          title: product.title,
          vendor: product.vendor,
          collections: collections.join(", "),
          issue: issueType
        });
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n⚠️ Trovati ${issues.length} prodotti con criticità di indicizzazione.`);
  console.table(issues.slice(0, 20));

  fs.writeFileSync("indexing_audit_results.json", JSON.stringify(issues, null, 2));
  
  if (issues.length > 0) {
    console.log("\n🚀 Avvio sistemazione automatica...");
    
    // Recuperiamo la mappa delle collezioni per gli spostamenti
    const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title } } }`);
    const colMap: Record<string, string> = {};
    colRes.data.collections.nodes.forEach((c: any) => { colMap[c.title.toLowerCase().trim()] = c.id; });

    const noPriceId = colMap["no price"];
    const ricambiId = colMap["tutti i ricambi"];
    const accessoriId = colMap["altri accessori"];
    const filtriId = colMap["filtri"];
    const pompeId = colMap["pompe per piscine"];
    const analisiId = colMap["analisi dell'acqua"];
    const chimicaId = colMap["prodotti chimici"];

    for (const issue of issues) {
      const title = issue.title.toLowerCase();
      let targetColId = null;

      if (title.includes("raccordo") || title.includes("tubo") || title.includes("valvola") || title.includes("tappo") || title.includes("skimmer") || title.includes("manicotto")) {
        targetColId = colMap["accessori per filtro"] || accessoriId;
      } else if (title.includes("spazzola") || title.includes("manico") || title.includes("retino") || title.includes("termometro") || title.includes("dosatore")) {
        targetColId = colMap["materiale di pulizia"] || accessoriId;
      } else if (title.includes("filtro") || title.includes("depuratore") || title.includes("cartuccia")) {
        targetColId = filtriId;
      } else if (title.includes("pompa") || title.includes("flopro")) {
        targetColId = pompeId;
      } else if (title.includes("batteria") || title.includes("sonda") || title.includes("blue connect") || title.includes("tester") || title.includes("analisi")) {
        targetColId = analisiId;
      } else if (title.includes("cloro") || title.includes("bromo") || title.includes("ossigeno") || title.includes("adesivo") || title.includes("gel")) {
        targetColId = chimicaId;
      }

      if (targetColId) {
        console.log(`✨ Fix: ${issue.title} -> categoria corretta`);
        const join = [targetColId];
        const leave = [];
        if (noPriceId) leave.push(noPriceId);
        
        // Rimuoviamo da categorie vasche se era mescolato
        if (issue.issue === "Accessorio mescolato con Piscine") {
          ["piscine fuori terra", "piscine in legno", "piscine in acciaio"].forEach(cat => {
            if (colMap[cat]) leave.push(colMap[cat]);
          });
        }

        await shopifyRequest(`mutation upd($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, {
          input: { id: issue.id, collectionsToJoin: join, collectionsToLeave: leave }
        });
        await new Promise(r => setTimeout(r, 200));
      }
    }
    console.log("✅ Sistemazione completata!");
  }
}

auditIndexing().catch(console.error);
