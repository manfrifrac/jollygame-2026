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

async function applyMasterCategorization() {
  const mapping = JSON.parse(fs.readFileSync("target_categorization.json", "utf8"));
  console.log(`🚀 Avvio Sincronizzazione Master di ${mapping.length} prodotti...`);

  let count = 0;
  for (const item of mapping) {
      if (item.new_category === "ALTRO") continue; // Saltiamo quelli non classificati per ora

      // Costruzione nuovi Tag
      let tags = item.old_tags.filter((t: string) => !t.startsWith("Categoria:") && !t.startsWith("Sottocategoria:"));
      tags.push(`Categoria:${item.new_category.charAt(0) + item.new_category.slice(1).toLowerCase().replace("_", " ")}`);
      
      if (item.new_sub && item.new_sub !== "Generico") {
          tags.push(`Sottocategoria:${item.new_sub}`);
      }

      // Special fix per nomi categorie (mappa verso handle Shopify esistenti)
      // Categoria:Trattamento -> Categoria:Trattamento acqua
      // Categoria:Filtraggio (già ok)
      // Categoria:Pulitori (già ok)
      tags = tags.map((t: string) => {
          if (t === "Categoria:Trattamento") return "Categoria:Trattamento acqua";
          return t;
      });

      const mutation = `
      mutation productUpdate($input: ProductInput!) {
        productUpdate(input: $input) {
          product { id }
          userErrors { message }
        }
      }
      `;

      const input = {
          id: item.id,
          tags: Array.from(new Set(tags)),
          productType: item.new_category.charAt(0) + item.new_category.slice(1).toLowerCase().replace("_", " ")
      };

      await shopifyRequest(mutation, { input });
      count++;
      
      if (count % 20 === 0) console.log(`   - Aggiornati ${count} prodotti...`);
  }

  console.log(`\n✅ Sincronizzazione completata! ${count} prodotti riorganizzati.`);
}

applyMasterCategorization().catch(console.error);
