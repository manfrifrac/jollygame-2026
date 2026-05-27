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

async function auditCategorization() {
  console.log("🔍 Avvio Audit Categorizzazione Globale...");

  let hasNextPage = true;
  let cursor = null;
  const report: any[] = [];

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          status
          vendor
          productType
          collections(first: 10) {
            nodes {
              title
              handle
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const collections = product.collections.nodes;
      const collectionHandles = collections.map((c: any) => c.handle);
      
      // Filtriamo i "falsi positivi" come le collezioni di servizio
      const realCollections = collections.filter((c: any) => 
          !["no-price", "frontpage", "all"].includes(c.handle)
      );

      if (realCollections.length === 0) {
        report.push({
          id: product.id,
          title: product.title,
          vendor: product.vendor,
          type: product.productType,
          status: product.status,
          issue: "UNCLASSIFIED"
        });
      } else if (realCollections.length === 1 && realCollections[0].handle === "piscine-fuori-terra") {
          // Prodotto solo nella categoria "Padre", non nelle sottocategorie
          report.push({
            id: product.id,
            title: product.title,
            vendor: product.vendor,
            type: product.productType,
            status: product.status,
            issue: "ONLY_PARENT_CATEGORY"
          });
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log("\n📊 RISULTATI AUDIT:");
  console.log(`❌ Non classificati: ${report.filter(r => r.issue === 'UNCLASSIFIED').length}`);
  console.log(`⚠️ Solo in categoria padre (Piscine): ${report.filter(r => r.issue === 'ONLY_PARENT_CATEGORY').length}`);

  // Analisi per vendor dei non classificati
  const unclassified = report.filter(r => r.issue === 'UNCLASSIFIED');
  const vendorStats = unclassified.reduce((acc: any, curr: any) => {
      acc[curr.vendor] = (acc[curr.vendor] || 0) + 1;
      return acc;
  }, {});
  
  console.log("\n🛑 Non classificati per Vendor:");
  console.table(vendorStats);

  // Esempi
  console.log("\n📝 Esempi di prodotti 'Sospesi':");
  console.table(report.slice(0, 15));

  fs.writeFileSync("categorization_audit.json", JSON.stringify(report, null, 2));
}

auditCategorization().catch(console.error);
