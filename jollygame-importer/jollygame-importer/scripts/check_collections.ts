import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkCollections() {
  const query = `{
    collections(first: 50) {
      nodes {
        id
        title
        handle
        productsCount { count }
        ruleSet {
          rules {
            column
            relation
            condition
          }
        }
      }
    }
  }`;

  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!
    },
    body: JSON.stringify({ query })
  });

  const data = await res.json();
  if (data.errors) {
      console.error("❌ Errore Shopify:", JSON.stringify(data.errors, null, 2));
      return;
  }
  const collections = data.data.collections.nodes;

  console.log("📂 ANALISI COLLEZIONI E FILTRI:");
  for (const c of collections) {
      console.log(`\n🔹 ${c.title} (${c.productsCount.count} prodotti)`);
      if (c.ruleSet) {
          console.log(`   Regole:`);
          c.ruleSet.rules.forEach((r: any) => {
              console.log(`    - ${r.column} ${r.relation} ${r.condition}`);
          });
      } else {
          console.log(`   (Collezione Manuale)`);
      }
  }
}

checkCollections().catch(console.error);
