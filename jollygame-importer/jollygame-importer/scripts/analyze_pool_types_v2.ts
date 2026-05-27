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

async function analyzePoolTypesDebug() {
  console.log("🔍 Avvio analisi tecnica dettagliata tipologie piscine (Debug Mode)...");

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
        // Logica di inclusione manuale se il filtro GraphQL fallisce
        const isPool = product.title.toLowerCase().includes("piscina") || 
                       product.productType?.toLowerCase() === "piscina" ||
                       ["Piscine Laghetto", "Gre"].includes(product.vendor) && product.title.toLowerCase().includes("piscina");
        
        if (isPool) {
            pools.push(product);
        }
    }
    
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`📦 Trovati ${pools.length} prodotti identificati come Piscine.`);

  const detailedAnalysis = pools.map(p => {
    const m = p.metafields.nodes;
    const findM = (key: string) => m.find((f: any) => f.key === key)?.value || "Non definito";

    return {
      title: p.title,
      brand: p.vendor,
      materiale: findM("materiale"),
      forma: findM("forma"),
      volume: findM("volume_acqua"),
      altezza: findM("altezza_vasca"),
      serie: findM("serie_prodotto")
    };
  });

  const summary = {
    per_materiale: {} as any,
    per_forma: {} as any,
    per_brand: {} as any
  };

  detailedAnalysis.forEach(p => {
    summary.per_materiale[p.materiale] = (summary.per_materiale[p.materiale] || 0) + 1;
    summary.per_forma[p.forma] = (summary.per_forma[p.forma] || 0) + 1;
    summary.per_brand[p.brand] = (summary.per_brand[p.brand] || 0) + 1;
  });

  console.log("\n📊 SINTESI TIPOLOGIE PISCINE:");
  console.log("\n--- Per Materiale ---");
  console.table(summary.per_materiale);
  console.log("\n--- Per Forma ---");
  console.table(summary.per_forma);
  console.log("\n--- Per Brand ---");
  console.table(summary.per_brand);

  fs.writeFileSync("detailed_pool_analysis.json", JSON.stringify(detailedAnalysis, null, 2));
}

analyzePoolTypesDebug().catch(console.error);
