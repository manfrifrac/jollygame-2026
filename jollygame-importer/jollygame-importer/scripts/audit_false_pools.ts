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

async function deepAuditFalsePools() {
  console.log("🔍 Ricerca 'falsi positivi' (accessori con parola Piscina nel titolo)...");

  let hasNextPage = true;
  let cursor = null;
  const allCandidates: any[] = [];

  while (hasNextPage) {
    const query = `
    query getPotentialPools($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
          status
          tags
        }
      }
    }
    `;
    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;
    
    for (const p of res.data.products.nodes) {
        const title = p.title.toLowerCase();
        const tags = p.tags;

        // Se è taggato come piscina o ha "piscina" nel titolo
        if (tags.includes("Categoria:Piscine") || title.includes("piscina")) {
            allCandidates.push(p);
        }
    }
    
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const falsePools: any[] = [];
  // Keyword che indicano un accessorio ANCHE se c'è scritto "Piscina"
  const accessoryKeywords = [
      "telo", "coperture", "copri", "tappeto", "scaletta", "pompa", "filtro", 
      "cartuccia", "skimmer", "tubo", "raccordo", "aspirafango", "retino", 
      "asta", "manico", "luce", "led", "termometro", "cloro", "ph", "chimic", 
      "accessori", "kit di pulizia", "toppa", "riparazione", "liner"
  ];

  for (const p of allCandidates) {
      const title = p.title.toLowerCase();
      
      // Se contiene una keyword accessoria E non è una piscina "vera" (es. set completo)
      // Spesso questi hanno titoli come "Telo per Piscina" o "Piscina Intex - Copertura"
      const isActuallyAccessory = accessoryKeywords.some(k => title.includes(k));
      
      // Se ha Categoria:Piscine ma è un accessorio -> DA SPOSTARE
      if (isActuallyAccessory) {
          // Eccezione: se il titolo è SOLO "Piscina [Modello]" va bene.
          // Se però contiene "Telo", "Pompa" ecc, è l'accessorio del modello.
          falsePools.push({
              id: p.id,
              title: p.title,
              status: p.status,
              tags: p.tags,
              vendor: p.vendor
          });
      }
  }

  console.log(`\n📊 Risultati:`);
  console.log(`⚠️  Falsi positivi (accessori mascherati da piscine) trovati: ${falsePools.length}`);

  if (falsePools.length > 0) {
      console.table(falsePools.map(p => ({ Titolo: p.title, Stato: p.status })));
  }

  fs.writeFileSync("false_pools_audit.json", JSON.stringify(falsePools, null, 2));
}

deepAuditFalsePools().catch(console.error);
