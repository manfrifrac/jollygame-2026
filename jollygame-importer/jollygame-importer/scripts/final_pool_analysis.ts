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

async function finalPoolAnalysis() {
  console.log("🔍 Avvio analisi tecnica finale tipologie piscine (Acciaio, Legno, Laghetto)...");

  let hasNextPage = true;
  let cursor = null;
  const pools: any[] = [];

  while (hasNextPage) {
    const query = `
    query getPools($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          vendor
          productType
          metafields(first: 20) {
            nodes {
              key
              value
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const title = product.title.toLowerCase();
        const vendor = product.vendor;
        
        // Identificazione Piscine (Gre Acciaio, Gre Legno, Laghetto)
        const isLaghetto = vendor === "Piscine Laghetto";
        const isGrePool = vendor === "Gre" && (title.includes("piscina") || title.includes("ovale") || title.includes("rotonda") || title.includes("rettangolare"));
        
        // Escludiamo esplicitamente i Robot e i Liner che hanno "piscina" nel titolo
        const isRobot = title.includes("robot") || title.includes("aspirapolvere") || title.includes("pulitore");
        const isComponent = title.includes("liner") || title.includes("copertura") || title.includes("telo") || title.includes("ricambio");

        if ((isLaghetto || isGrePool) && !isRobot && !isComponent) {
            pools.push(product);
        }
    }
    
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`📦 Trovate ${pools.length} Piscine reali identificate.`);

  const detailedAnalysis = pools.map(p => {
    const m = p.metafields.nodes;
    const findM = (key: string) => m.find((f: any) => f.key === key)?.value || "Non definito";

    let cat = "Altro";
    if (p.vendor === "Piscine Laghetto") cat = "Laghetto Design";
    else if (findM("materiale") === "Acciaio" || p.title.toLowerCase().includes("acciaio")) cat = "Gre Acciaio";
    else if (findM("materiale") === "Legno" || p.title.toLowerCase().includes("legno")) cat = "Gre Legno";
    else if (p.title.toLowerCase().includes("composito")) cat = "Gre Composito";

    return {
      title: p.title,
      brand: p.vendor,
      categoria_tecnica: cat,
      materiale: findM("materiale"),
      forma: findM("forma"),
      volume: findM("volume_acqua"),
      altezza: findM("altezza_vasca"),
      serie: findM("serie_prodotto")
    };
  });

  const stats = {
    per_categoria: {} as any,
    per_forma: {} as any
  };

  detailedAnalysis.forEach(p => {
    stats.per_categoria[p.categoria_tecnica] = (stats.per_categoria[p.categoria_tecnica] || 0) + 1;
    stats.per_forma[p.forma] = (stats.per_forma[p.forma] || 0) + 1;
  });

  console.log("\n📊 SINTESI FINALE PISCINE:");
  console.table(stats.per_categoria);
  console.table(stats.per_forma);

  fs.writeFileSync("final_pool_analysis.json", JSON.stringify(detailedAnalysis, null, 2));
}

finalPoolAnalysis().catch(console.error);
