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

async function auditEveryCategory() {
  console.log("🔍 Inizio Audit Granulare di TUTTE le categorie (una per una)...");

  const colRes = await shopifyRequest(`{ collections(first: 100) { nodes { id title handle } } }`);
  const collections = colRes.data.collections.nodes.filter((c: any) => 
      !["no-price", "frontpage", "all"].includes(c.handle)
  );

  const fullReport: any = {};

  for (const col of collections) {
      console.log(`\n📂 Analisi Collezione: ${col.title} (${col.handle})`);
      
      const prodRes = await shopifyRequest(`
      {
        collection(id: "${col.id}") {
          products(first: 250) {
            nodes {
              id
              title
              tags
              vendor
            }
          }
        }
      }
      `);

      const products = prodRes.data?.collection?.products?.nodes || [];
      const intruders: any[] = [];

      // Definizione regole per questa categoria
      for (const p of products) {
          const title = p.title.toLowerCase();
          const handle = col.handle;
          let isIntruder = false;
          let reason = "";

          // --- LOGICA DI ESCLUSIONE PER CATEGORIA ---
          
          if (handle.includes("pulitori")) {
              if (["telo", "copertura", "piscina ", "liner", "cloro", "bromo", "pompa di calore"].some(k => title.includes(k) && !title.includes("robot") && !title.includes("pulitore"))) {
                  isIntruder = true;
                  reason = "Sembra un accessorio o una vasca, non un pulitore";
              }
          }

          if (handle.includes("trattamento") || handle.includes("chimici")) {
              if (["robot", "pompa di calore", "piscina ", "telo", "scaletta"].some(k => title.includes(k))) {
                  isIntruder = true;
                  reason = "Prodotto non chimico/trattamento";
              }
          }

          if (handle.includes("filtraggio") || handle.includes("filtri")) {
              if (["pompa di calore", "riscaldamento", "cloro", "bromo", "robot", "piscina "].some(k => title.includes(k) && !title.includes("pompa") && !title.includes("filtro"))) {
                  isIntruder = true;
                  reason = "Non sembra un sistema di filtraggio";
              }
          }

          if (handle.includes("piscine-")) { // Sottocategorie piscine (acciaio, legno, ecc)
              const accessoryKeywords = ["telo", "copertura", "copri", "tappeto", "scaletta", "pompa", "filtro", "raccordo", "tubo", "adesivo", "tester"];
              if (accessoryKeywords.some(k => title.includes(k))) {
                  isIntruder = true;
                  reason = "Accessorio in categoria vasche";
              }
          }

          if (isIntruder) {
              intruders.push({ title: p.title, reason });
          }
      }

      fullReport[col.title] = {
          total: products.length,
          intruders: intruders
      };

      if (intruders.length > 0) {
          console.log(`   ⚠️ Trovati ${intruders.length} sospetti:`);
          intruders.forEach(i => console.log(`      - ${i.title} [${i.reason}]`));
      } else {
          console.log(`   ✅ Collezione pulita.`);
      }
  }

  fs.writeFileSync("exhaustive_category_report.json", JSON.stringify(fullReport, null, 2));
}

auditEveryCategory().catch(console.error);
