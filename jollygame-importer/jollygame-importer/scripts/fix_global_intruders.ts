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

async function fixGlobalIntruders() {
  const intruders = JSON.parse(fs.readFileSync("global_intruders_audit.json", "utf8"));
  console.log(`🛠️ Avvio pulizia globale di ${intruders.length} intrusi...`);

  for (const product of intruders) {
      const title = product.title.toLowerCase();
      let tags: string[] = product.tags;
      
      // 1. Pulizia dei tag Categoria/Sottocategoria incoerenti
      // Rimuoviamo i tag che hanno causato l'intrusione
      if (product.current_category === "Pulitori") {
          tags = tags.filter(t => t !== "Categoria:Pulitori" && !t.startsWith("Sottocategoria:Pulitori"));
      } else if (product.current_category === "Trattamento acqua") {
          tags = tags.filter(t => t !== "Categoria:Trattamento acqua" && !t.startsWith("Sottocategoria:Prodotti chimici"));
      } else if (product.current_category === "Filtraggio") {
          tags = tags.filter(t => t !== "Categoria:Filtraggio" && !t.startsWith("Sottocategoria:Filtri") && !t.startsWith("Sottocategoria:Pompe"));
      }

      // 2. Riassegnazione corretta
      const newTags = new Set(tags);

      // PISCINE (se erano finite in pulitori)
      if (title.includes("piscina") && !title.includes("robot") && !title.includes("pulitore") && !title.includes("copertura")) {
          newTags.add("Categoria:Piscine");
          if (title.includes("acciaio") || ["bora bora"].some(k => title.includes(k))) newTags.add("Sottocategoria:Piscine in acciaio");
          if (title.includes("pietra") || title.includes("sumatra")) newTags.add("Sottocategoria:Piscine in acciaio"); // Sumatra è acciaio con decoro pietra
      }

      // COPERTURE
      if (title.includes("copertura") || title.includes("telo")) {
          newTags.add("Categoria:Coperture");
          if (title.includes("invernale")) newTags.add("Sottocategoria:Copertura invernale");
      }

      // TRATTAMENTO (se finiti in pulitori)
      if (title.includes("kit trattamento") || title.includes("bromo") || title.includes("cloro")) {
          newTags.add("Categoria:Trattamento acqua");
          newTags.add("Sottocategoria:Prodotti chimici");
      }

      // RISCALDAMENTO
      if (title.includes("pompa di calore")) {
          newTags.add("Categoria:Riscaldamento");
          newTags.add("Sottocategoria:Pompe di calore");
      }

      // ILLUMINAZIONE
      if (title.includes("proiettore") || title.includes("led")) {
          newTags.add("Categoria:Accessori");
          newTags.add("Sottocategoria:Illuminazione");
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

  console.log("\n✅ Bonifica globale completata!");
}

fixGlobalIntruders().catch(console.error);
