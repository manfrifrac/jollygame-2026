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

async function auditPoolIntruders() {
  console.log("🔍 Analisi 'intrusi' nella categoria Piscine...");

  let hasNextPage = true;
  let cursor = null;
  const poolProducts: any[] = [];

  while (hasNextPage) {
    const query = `
    query getPools($cursor: String) {
      products(first: 250, after: $cursor, query: "tag:'Categoria:Piscine'") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
          tags
          productType
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        poolProducts.push(product);
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const intruders: any[] = [];
  const poolKeywords = ["piscina", "ovale", "rotonda", "rettangolare", "tonda", "quadrata", "lili", "grenade", "marbella", "vermela", "city", "mint", "sicilia", "pacific", "fidji", "bora bora", "haiti", "atlantis", "steel", "mauritius", "varadero", "granada", "avantgarde", "easy set", "prisma", "ultra xtr", "graphite"];
  
  // Se il titolo contiene queste parole, NON è una piscina ma un intruso
  const intruderKeywords = ["copertura", "telo", "liner", "robot", "pulitore", "spazzola", "filtro", "pompa", "motore", "raccordo", "tubo", "adesivo", "tester", "analisi", "cloro", "bromo", "svernante", "anticalcare", "trattamento", "accessori", "kit di pulizia", "aspiratore", "manuale", "ricambio", "pezzo", "guarnizione", "vite", "bullone", "tappo", "regolatore", "plug", "casetta", "proiettore", "led", "lampada"];

  for (const p of poolProducts) {
      const title = p.title.toLowerCase();
      
      const hasIntruderWord = intruderKeywords.some(k => title.includes(k));
      const hasPoolWord = poolKeywords.some(k => title.includes(k));

      // Se ha una parola da intruso, o NON ha parole da piscina, è sospetto
      if (hasIntruderWord || !hasPoolWord) {
          // Eccezione: titoli tipo "Piscina Ovale" che contengono "Ovale" (poolKeyword) ma magari anche "Liner" (intruder)
          // Se la parola "piscina" è seguita da "copertura", "liner" ecc, è l'accessorio.
          
          // Se "piscina" è presente ma è "Copertura per piscina", è un intruso.
          const isAccessory = intruderKeywords.some(k => title.includes(`${k} per piscina`) || title.includes(`${k} piscina`));
          
          if (isAccessory || (hasIntruderWord && !title.startsWith("piscina"))) {
            intruders.push({
                id: p.id,
                title: p.title,
                vendor: p.vendor,
                current_tags: p.tags,
                reason: isAccessory ? "Accessorio esplicito" : "Keyword intrusa rilevata"
            });
          }
      }
  }

  console.log(`\n📊 Analisi completata.`);
  console.log(`✅ Prodotti totali con tag 'Categoria:Piscine': ${poolProducts.length}`);
  console.log(`⚠️  Intrusi identificati: ${intruders.length}`);

  fs.writeFileSync("pool_intruders_audit.json", JSON.stringify(intruders, null, 2));
  console.log("\n📝 Report salvato in 'pool_intruders_audit.json'");
  
  if (intruders.length > 0) {
      console.log("\n❌ ESEMPI DI INTRUSI DA SPOSTARE:");
      intruders.slice(0, 10).forEach(i => console.log(` - ${i.title} (${i.reason})`));
  }
}

auditPoolIntruders().catch(console.error);
