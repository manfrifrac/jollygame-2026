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

async function checkOnlineVisibility() {
  console.log("🔍 Analisi visibilità reale del catalogo online...");

  let hasNextPage = true;
  let cursor = null;
  const visibilityReport: any[] = [];

  // Recuperiamo le pubblicazioni (canali di vendita) per capire quali ID corrispondono a cosa
  const pubQuery = `{ publications(first: 10) { nodes { id name } } }`;
  const pubRes = await shopifyRequest(pubQuery);
  const channels = pubRes.data?.publications?.nodes || [];
  console.log("Canali rilevati:", channels.map((c: any) => c.name).join(", "));

  while (hasNextPage) {
    const query = `
    query getVisibility($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          status
          mediaCount { count }
          totalVariants
          resourcePublicationsV2(first: 10) {
            nodes {
              publication { name }
              isPublished
            }
          }
          variants(first: 1) {
            nodes {
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

    const products = res.data.products.nodes;
    for (const product of products) {
      const isOnline = product.resourcePublicationsV2.nodes.some(
        (p: any) => p.publication.name.toLowerCase().includes("online store") && p.isPublished
      );
      
      const price = parseFloat(product.variants.nodes[0]?.price || "0");
      
      visibilityReport.push({
        title: product.title,
        handle: product.handle,
        status: product.status,
        has_images: product.mediaCount.count > 0,
        price: price,
        sku: product.variants.nodes[0]?.sku || null,
        is_visible_online: isOnline,
        is_sellable: isOnline && price > 0 && product.status === "ACTIVE"
      });
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const stats = {
    total: visibilityReport.length,
    active: visibilityReport.filter(p => p.status === "ACTIVE").length,
    draft: visibilityReport.filter(p => p.status === "DRAFT").length,
    archived: visibilityReport.filter(p => p.status === "ARCHIVED").length,
    visible_online: visibilityReport.filter(p => p.is_visible_online).length,
    sellable: visibilityReport.filter(p => p.is_sellable).length,
    zero_price: visibilityReport.filter(p => p.price === 0).length,
    no_images: visibilityReport.filter(p => !p.has_images).length
  };

  console.log("\n📊 STATO REALE DEL CATALOGO:");
  console.table(stats);

  fs.writeFileSync("catalog_visibility_report.json", JSON.stringify({ stats, details: visibilityReport }, null, 2));
  console.log("\n✅ Analisi completata. Report salvato in 'catalog_visibility_report.json'");
  
  if (stats.sellable === 0) {
      console.log("\n🛑 ATTENZIONE: Nessun prodotto è attualmente vendibile online (Prezzo > 0 + Stato ACTIVE + Canale Online attivo).");
  } else {
      console.log(`\n🚀 Solo ${stats.sellable} prodotti su ${stats.total} sono effettivamente acquistabili dai clienti.`);
  }
}

checkOnlineVisibility().catch(console.error);
