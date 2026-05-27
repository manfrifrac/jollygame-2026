import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
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

async function detailedCollectionAudit() {
  console.log("🔍 Analisi Dettagliata Collezioni per Pulizia Duplicati...");

  const query = `
  {
    collections(first: 100) {
      nodes {
        id
        title
        handle
        productsCount { count }
        image { url }
        ruleSet {
          rules {
            column
            relation
            condition
          }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  
  if (res.errors) {
    console.error("Errore GraphQL:", JSON.stringify(res.errors, null, 2));
    return;
  }

  const collections = res.data?.collections?.nodes;

  if (!collections) {
    console.log("Nessuna collezione trovata.");
    return;
  }

  const duplicates: any = {};
  collections.forEach((c: any) => {
    const title = c.title.toLowerCase();
    if (!duplicates[title]) duplicates[title] = [];
    duplicates[title].push(c);
  });

  console.log("\n⚠️ COLLEZIONI DUPLICATE IDENTIFICATE:");
  for (const title in duplicates) {
    if (duplicates[title].length > 1) {
      console.log(`\n📂 Titolo: "${title.toUpperCase()}"`);
      duplicates[title].forEach((c: any) => {
        const rules = c.ruleSet?.rules ? c.ruleSet.rules.map((r: any) => `${r.column} ${r.relation} ${r.condition}`).join(", ") : "MANUALE";
        console.log(`  - Handle: ${c.handle}`);
        console.log(`    Prodotti: ${c.productsCount.count}`);
        console.log(`    Regole: ${rules}`);
        console.log(`    Immagine (Icona): ${c.image?.url || "Nessuna"}`);
      });
    }
  }

  console.log("\n✅ Analisi completata.");
}

detailedCollectionAudit().catch(console.error);
