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

async function applyMasterCategorizationV2() {
  const mapping = JSON.parse(fs.readFileSync("target_categorization.json", "utf8"));
  console.log(`🚀 Avvio Sincronizzazione Master V2 (Allineamento Tag Esatti) di ${mapping.length} prodotti...`);

  let count = 0;
  for (const item of mapping) {
      if (item.new_category === "ALTRO") continue;

      // 1. Pulizia vecchi tag di categoria
      let tags = item.old_tags.filter((t: string) => !t.startsWith("Categoria:") && !t.startsWith("Sottocategoria:"));
      
      // 2. Mapping Categorie (Padre)
      const catMap: Record<string, string> = {
          PISCINE: "Categoria:Piscine",
          PULITORI: "Categoria:Pulitori",
          TRATTAMENTO: "Categoria:Trattamento acqua",
          FILTRAGGIO: "Categoria:Filtraggio",
          RISCALDAMENTO: "Categoria:Riscaldamento",
          ACCESSORI: "Categoria:Accessori"
      };
      tags.push(catMap[item.new_category]);

      // 3. Mapping Sottocategorie (Figlio) - Devono corrispondere alle regole delle Collezioni Automatiche
      if (item.new_category === "RISCALDAMENTO") {
          tags.push("Sottocategoria:Pompe di calore");
      }

      if (item.new_category === "TRATTAMENTO") {
          tags.push("Sottocategoria:Prodotti chimici");
      }

      if (item.new_sub && item.new_sub !== "Generico") {
          const subMap: Record<string, string> = {
              "Acciaio": "Sottocategoria:Piscine in acciaio",
              "Legno": "Sottocategoria:Piscine in legno",
              "Composito": "Sottocategoria:Piscine in composito",
              "Elettrici (Robot)": "Sottocategoria:Pulitori elettrico",
              "Manuali/Idraulici": "Sottocategoria:Pulitori manuali",
              "Pompe": "Sottocategoria:Pompe per piscine",
              "Filtri e Idraulica": "Sottocategoria:Filtri",
              "Coperture": "Sottocategoria:Copertura invernale",
              "Liner": "Sottocategoria:Liner e riparatori",
              "Scalette": "Sottocategoria:Scalette",
              "Docce": "Sottocategoria:Docce",
              "Illuminazione": "Sottocategoria:Illuminazione"
          };
          
          if (subMap[item.new_sub]) {
              tags.push(subMap[item.new_sub]);
          }
      }

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
          productType: item.new_category === "TRATTAMENTO" ? "Trattamento acqua" : item.new_category.charAt(0) + item.new_category.slice(1).toLowerCase()
      };

      await shopifyRequest(mutation, { input });
      count++;
      
      if (count % 20 === 0) console.log(`   - Aggiornati ${count} prodotti...`);
  }

  console.log(`\n✅ Sincronizzazione V2 completata! ${count} prodotti allineati ai tag delle collezioni.`);
}

applyMasterCategorizationV2().catch(console.error);
