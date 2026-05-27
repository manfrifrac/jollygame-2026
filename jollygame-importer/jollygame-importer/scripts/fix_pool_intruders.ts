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

async function fixIntruders() {
  const intruders = JSON.parse(fs.readFileSync("pool_intruders_audit.json", "utf8"));
  console.log(`🛠️ Avvio spostamento di ${intruders.length} intrusi...`);

  for (const product of intruders) {
      const title = product.title.toLowerCase();
      const currentTags: string[] = product.current_tags;
      
      // 1. Rimuoviamo i tag sbagliati legati alle piscine
      let newTags = currentTags.filter(t => 
          t !== "Categoria:Piscine" && 
          !t.startsWith("Sottocategoria:Piscine")
      );

      // 2. Aggiungiamo i tag corretti in base alle keyword
      if (title.includes("copertura") || title.includes("telo") || title.includes("copertore")) {
          newTags.push("Categoria:Coperture");
          if (title.includes("invernale")) newTags.push("Sottocategoria:Copertura invernale");
          else if (title.includes("isotermica") || title.includes("termico")) newTags.push("Sottocategoria:Coperture isotermiche");
      }
      else if (title.includes("pulitore") || title.includes("robot") || title.includes("aspiratore") || title.includes("spazzola") || title.includes("retino")) {
          newTags.push("Categoria:Pulitori");
          if (title.includes("robot") || title.includes("elettrico")) newTags.push("Sottocategoria:Pulitori elettrico");
          else newTags.push("Sottocategoria:Pulitori manuali");
      }
      else if (title.includes("liner") || title.includes("riparazione") || title.includes("adesivo")) {
          newTags.push("Sottocategoria:Liner e riparatori");
      }
      else if (title.includes("filtro") || title.includes("pompa") || title.includes("raccordo") || title.includes("tubo")) {
          newTags.push("Categoria:Filtraggio");
          if (title.includes("pompa")) newTags.push("Sottocategoria:Pompe per piscine");
          else newTags.push("Sottocategoria:Filtri");
          
          if (title.includes("raccordo") || title.includes("tubo")) {
              newTags.push("Categoria:Accessori");
              newTags.push("Sottocategoria:Altri accessori");
          }
      }
      else if (title.includes("cloro") || title.includes("bromo") || title.includes("trattamento") || title.includes("tester")) {
          newTags.push("Categoria:Trattamento acqua");
          newTags.push("Sottocategoria:Prodotti chimici");
      }
      else {
          // Fallback generico per accessori non categorizzati
          newTags.push("Categoria:Accessori");
          newTags.push("Sottocategoria:Altri accessori");
      }

      // Rendi i tag unici
      newTags = Array.from(new Set(newTags));

      console.log(`✨ Spostando: ${product.title}`);
      console.log(`   - Vecchi Tag: ${currentTags.filter(t => t.startsWith("Categoria") || t.startsWith("Sottocategoria")).join(", ")}`);
      console.log(`   - Nuovi Tag:  ${newTags.filter(t => t.startsWith("Categoria") || t.startsWith("Sottocategoria")).join(", ")}`);

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
              tags: newTags
          }
      });
  }

  console.log("\n✅ Bonifica intrusi completata!");
}

fixIntruders().catch(console.error);
