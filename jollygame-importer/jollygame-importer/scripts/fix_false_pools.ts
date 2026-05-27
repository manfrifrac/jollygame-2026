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

async function fixFalsePools() {
  const falsePools = JSON.parse(fs.readFileSync("false_pools_audit.json", "utf8"));
  console.log(`🛠️ Avvio spostamento di ${falsePools.length} falsi positivi dalle Piscine...`);

  for (const product of falsePools) {
      const title = product.title.toLowerCase();
      let tags: string[] = product.tags;
      
      // 1. Rimuoviamo i tag sbagliati legati alle piscine
      tags = tags.filter(t => 
          t !== "Categoria:Piscine" && 
          !t.startsWith("Sottocategoria:Piscine")
      );

      const newTags = new Set(tags);

      // 2. Riassegnazione corretta
      if (title.includes("copertura") || title.includes("telo") || title.includes("copri") || title.includes("avvolgitore")) {
          newTags.add("Categoria:Coperture");
      }
      else if (title.includes("pulitore") || title.includes("kit di pulizia") || title.includes("aspiratore") || title.includes("spazzola")) {
          newTags.add("Categoria:Pulitori");
          newTags.add("Sottocategoria:Pulitori manuali");
      }
      else if (title.includes("liner") || title.includes("riparazione") || title.includes("toppa") || title.includes("adesivo")) {
          newTags.add("Sottocategoria:Liner e riparatori");
      }
      else if (title.includes("filtro") || title.includes("pompa") || title.includes("depuratore") || title.includes("cartuccia") || title.includes("skimmer") || title.includes("giunzione")) {
          newTags.add("Categoria:Filtraggio");
          if (title.includes("pompa")) newTags.add("Sottocategoria:Pompe per piscine");
          else newTags.add("Sottocategoria:Filtri");
      }
      else if (title.includes("scaletta")) {
          newTags.add("Sottocategoria:Scalette");
      }
      else if (title.includes("illuminazione") || title.includes("led") || title.includes("proiettore")) {
          newTags.add("Sottocategoria:Illuminazione");
      }
      else if (title.includes("tappeto")) {
          newTags.add("Sottocategoria:Tappeti");
      }
      else {
          newTags.add("Categoria:Accessori");
          newTags.add("Sottocategoria:Altri accessori");
      }

      const finalTags = Array.from(newTags);

      console.log(`✨ Correzione: ${product.title}`);
      
      const mutation = `
      mutation productUpdate($input: ProductInput!) {
        productUpdate(input: $input) {
          product { id }
          userErrors { message }
        }
      }
      `;

      await shopifyRequest(mutation, {
          input: {
              id: product.id,
              tags: finalTags
          }
      });
  }

  console.log("\n✅ Pulizia 'falsi positivi' completata!");
}

fixFalsePools().catch(console.error);
