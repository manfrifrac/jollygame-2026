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

async function auditOnlineProducts() {
  console.log("🔍 Audit approfondito dei 124 prodotti attualmente ONLINE...");

  let hasNextPage = true;
  let cursor = null;
  const onlineAudit: any[] = [];
  const activeButNotSellable: any[] = [];

  while (hasNextPage) {
    const query = `
    query getOnline($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          status
          vendor
          descriptionHtml
          mediaCount { count }
          resourcePublicationsV2(first: 10) {
            nodes {
              publication { name }
              isPublished
            }
          }
          variants(first: 5) {
            nodes {
              price
              sku
            }
          }
          metafields(first: 10, namespace: "custom") {
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
      const isOnline = product.resourcePublicationsV2.nodes.some(
        (p: any) => p.publication.name.toLowerCase().includes("online store") && p.isPublished
      );
      const price = parseFloat(product.variants.nodes[0]?.price || "0");
      const isSellable = isOnline && price > 0 && product.status === "ACTIVE";

      if (isSellable) {
        const issues: string[] = [];
        if (product.mediaCount.count === 0) issues.push("MISSING_IMAGES");
        if (!product.descriptionHtml || product.descriptionHtml.length < 50) issues.push("SHORT_OR_MISSING_DESCRIPTION");
        
        const metafieldCount = product.metafields.nodes.length;
        if (metafieldCount < 2) issues.push("POOR_TECHNICAL_SPECS");

        onlineAudit.push({
          title: product.title,
          handle: product.handle,
          vendor: product.vendor,
          price: price,
          issues: issues
        });
      } else if (product.status === "ACTIVE") {
          activeButNotSellable.push({
              title: product.title,
              price: price,
              isOnline: isOnline,
              reason: price <= 0 ? "ZERO_PRICE" : (!isOnline ? "NOT_PUBLISHED_ONLINE" : "UNKNOWN")
          });
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log("\n✅ Prodotti ONLINE (Vendibili):", onlineAudit.length);
  const issuesFound = onlineAudit.filter(p => p.issues.length > 0);
  console.log("⚠️ Prodotti con potenziali problemi qualitativi:", issuesFound.length);
  
  if (issuesFound.length > 0) {
      console.table(issuesFound.slice(0, 10)); // Mostra i primi 10
  }

  console.log("\n🛑 Prodotti ATTIVI ma NON VENDIBILI:", activeButNotSellable.length);
  if (activeButNotSellable.length > 0) {
      console.table(activeButNotSellable);
  }

  fs.writeFileSync("online_audit_report.json", JSON.stringify({ online: onlineAudit, anomalies: activeButNotSellable }, null, 2));
}

auditOnlineProducts().catch(console.error);
