import dotenv from "dotenv";

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

async function deepAuditActive() {
  console.log("🔍 Audit tecnico approfondito prodotti ONLINE...");

  let hasNextPage = true;
  let cursor = null;

  while (hasNextPage) {
    const query = `
    query getActive($cursor: String) {
      products(first: 250, after: $cursor, query: "status:active") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          metafields(first: 20, namespace: "custom") {
            nodes {
              key
              value
              type
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        let suspicious = false;
        const metaIssues: string[] = [];

        for (const m of product.metafields.nodes) {
            // Controllo 1: Metaobject list malformate (devono essere array JSON di GID)
            if (m.key.includes("ricambi") || m.key.includes("lista")) {
                try {
                    const parsed = JSON.parse(m.value);
                    if (!Array.isArray(parsed)) {
                        metaIssues.push(`Metafield ${m.key} non è un array`);
                        suspicious = true;
                    } else if (parsed.some(item => typeof item !== 'string' || !item.startsWith("gid://"))) {
                        metaIssues.push(`Metafield ${m.key} contiene GID non validi`);
                        suspicious = true;
                    }
                } catch (e) {
                    metaIssues.push(`Metafield ${m.key} JSON corrotto: ${m.value}`);
                    suspicious = true;
                }
            }

            // Controllo 2: Valori "null" o stringhe AI rimaste nei metafields
            if (m.value.toLowerCase().includes("rispondi solo con") || m.value === "null") {
                metaIssues.push(`Metafield ${m.key} contiene residui AI/null`);
                suspicious = true;
            }
        }

        if (suspicious) {
            console.log(`\n❌ SOSPETTO: ${product.title} (${product.handle})`);
            metaIssues.forEach(issue => console.log(`   - ${issue}`));
        }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log("\n✅ Audit tecnico completato.");
}

deepAuditActive().catch(console.error);
