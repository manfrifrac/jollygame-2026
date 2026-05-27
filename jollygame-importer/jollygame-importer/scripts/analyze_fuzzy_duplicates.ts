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

function normalizeTitle(title: string) {
    return title
        .toLowerCase()
        .replace(/aspirapolvere|robot|piscina|pulitore|filtro/gi, "") // Rimuoviamo stop-words comuni
        .replace(/[^a-z0-9]/g, "") // Rimuoviamo punteggiatura e spazi
        .trim();
}

async function analyzeFuzzyDuplicates() {
  console.log("🔍 Analisi avanzata duplicati (Fuzzy Matching)...");

  let hasNextPage = true;
  let cursor = null;
  const productGroups: Record<string, any[]> = {};

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          mediaCount { count }
          status
          descriptionHtml
          variants(first: 1) {
            nodes {
              id
              price
              sku
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const key = normalizeTitle(product.title);
        if (key === "") continue; // Evitiamo chiavi vuote se il titolo era solo stop-words
        if (!productGroups[key]) productGroups[key] = [];
        productGroups[key].push(product);
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const report: any[] = [];

  for (const [key, products] of Object.entries(productGroups)) {
    if (products.length > 1) {
      // Ordiniamo per decidere il "vincitore"
      const sorted = products.sort((a, b) => {
        const priceA = parseFloat(a.variants.nodes[0]?.price || "0");
        const priceB = parseFloat(b.variants.nodes[0]?.price || "0");
        
        if (priceA !== priceB) return priceB - priceA;
        if (a.mediaCount.count !== b.mediaCount.count) return b.mediaCount.count - a.mediaCount.count;
        // Se tutto è uguale, premiamo la descrizione più lunga
        return (b.descriptionHtml?.length || 0) - (a.descriptionHtml?.length || 0);
      });

      report.push({
        normalized_key: key,
        winner: {
            id: sorted[0].id,
            title: sorted[0].title,
            price: sorted[0].variants.nodes[0]?.price,
            images: sorted[0].mediaCount.count
        },
        duplicates: sorted.slice(1).map(p => ({
            id: p.id,
            title: p.title,
            price: p.variants.nodes[0]?.price,
            images: p.mediaCount.count
        }))
      });
    }
  }

  fs.writeFileSync("fuzzy_duplicates_report.json", JSON.stringify(report, null, 2));
  console.log(`\n✅ Analisi completata. Trovati ${report.length} gruppi di duplicati sospetti.`);
  console.log("Visualizzazione primi 10 gruppi:");
  console.table(report.slice(0, 10).map(r => ({
      Key: r.normalized_key,
      Winner: r.winner.title,
      Dups: r.duplicates.length
  })));
}

analyzeFuzzyDuplicates().catch(console.error);
