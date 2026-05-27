import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

const AUDIT_QUERY = `
query {
  products(first: 250, query: "status:ACTIVE") {
    nodes {
      title
      tags
      collections(first: 10) {
        nodes {
          title
        }
      }
    }
  }
}
`;

async function main() {
  const res = await shopifyRequest(AUDIT_QUERY);
  const products = res.data?.products?.nodes || [];
  
  console.log("--- AUDIT FINALE: CATEGORIZZAZIONE ---");
  const report = {
      conflitti: [] as any[],
      stats: { piscine: 0, filtri: 0, accessori: 0 }
  };

  products.forEach(p => {
      const colls = p.collections.nodes.map(c => c.title.toLowerCase());
      const hasPiscine = colls.some(t => t.includes('piscine'));
      const hasFiltro = colls.some(t => t.includes('filtraggio') || t.includes('filtri') || t.includes('pompe'));
      const hasAccessori = colls.some(t => t.includes('accessori') || t.includes('coperture'));

      if (hasPiscine && (hasFiltro || hasAccessori)) {
          report.conflitti.push({ title: p.title, colls });
      }
      if (hasPiscine) report.stats.piscine++;
      if (hasFiltro) report.stats.filtri++;
      if (hasAccessori) report.stats.accessori++;
  });
  
  console.log(JSON.stringify(report, null, 2));
}

main().catch(console.error);
