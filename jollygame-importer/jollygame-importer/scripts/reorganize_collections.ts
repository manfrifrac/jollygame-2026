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
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function reorganizeCollections() {
  console.log("🚀 Avvio riorganizzazione Collezioni su Shopify...");

  // 1. Carichiamo il mapping suggerito
  const reviewData = JSON.parse(fs.readFileSync("product_category_review.json", "utf-8"));

  // 2. Recuperiamo tutte le collezioni esistenti per mappare Titolo -> ID
  const pubQuery = `{ collections(first: 250) { nodes { id title handle } } }`;
  const pubRes = await shopifyRequest(pubQuery);
  const collections = pubRes.data.collections.nodes;
  const colMap: Record<string, string> = {};
  collections.forEach((c: any) => { colMap[c.title.toLowerCase()] = c.id; });

  // Mappatura manuale tra categorie suggerite e nomi collezioni reali
  const catToCol: Record<string, string> = {
    "Pulitori > Elettrici": "Pulitori elettrico",
    "Pulitori > Manuali": "Pulitori manuali",
    "Riscaldamento > Pompe di Calore": "Pompe di calore",
    "Trattamento Acqua > Elettrolisi": "Trattamento acqua",
    "Trattamento Acqua > Sistemi UV": "Disinfezione per UV",
    "Trattamento Acqua > Analisi e Controllo": "Analisi dell'acqua",
    "Trattamento Acqua > Prodotti Chimici": "Prodotti chimici",
    "Piscine > Legno": "Piscine in legno",
    "Piscine > Acciaio": "Piscine in acciaio",
    "Piscine > Composito": "Piscine in composito",
    "Piscine > Interrate": "Piscine interrate",
    "Componenti > Liner": "Liner e riparatori",
    "Componenti > Coperture": "Coperture",
    "Filtrazione > Filtri": "Filtri",
    "Filtrazione > Pompe": "Pompe per piscine",
    "Componenti > Scalette": "Scalette",
    "Accessori > Manutenzione": "Altri accessori"
  };

  const noPriceId = colMap["no price"];
  let updatedCount = 0;

  for (const item of reviewData) {
    const targetColName = catToCol[item.suggested_category];
    const targetColId = targetColName ? colMap[targetColName.toLowerCase()] : null;

    if (targetColId) {
      console.log(`📦 Spostamento: ${item.title} -> [${targetColName}]`);
      
      // Aggiungiamo alla nuova collezione e rimuoviamo da "no-price" se presente
      const mutation = `
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id }
            userErrors { field message }
          }
        }
      `;

      const input: any = {
          id: item.id,
          collectionsToJoin: [targetColId]
      };
      
      if (noPriceId) {
          input.collectionsToLeave = [noPriceId];
      }

      const res = await shopifyRequest(mutation, { input });
      if (res.data?.productUpdate?.product) {
          updatedCount++;
          process.stdout.write(".");
      } else {
          console.error(`\n❌ Errore per ${item.title}:`, JSON.stringify(res.data?.productUpdate?.userErrors));
      }
      
      await new Promise(r => setTimeout(r, 300));
    }
  }

  console.log(`\n\n✅ Riorganizzazione completata! ${updatedCount} prodotti ricategorizzati.`);
}

reorganizeCollections().catch(console.error);
