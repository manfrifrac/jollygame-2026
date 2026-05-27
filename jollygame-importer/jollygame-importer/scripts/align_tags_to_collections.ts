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

async function alignTagsToCollections() {
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  const greProducts = data.filter((p: any) => p.vendor === "Gre");

  console.log(`🎯 Allineamento Tag per ${greProducts.length} prodotti Gre...`);

  let updatedCount = 0;

  for (const p of greProducts) {
      const title = p.title.toLowerCase();
      const sku = (p.variants.nodes[0]?.sku || "").toUpperCase();
      const tags: string[] = p.tags || [];
      const newTags = new Set(tags);

      // 1. Categoria:Piscine
      if (title.includes("piscina gre") || title.includes("serie")) {
          newTags.add("Categoria:Piscine");
          // Sottocategorie specifiche Gre
          if (title.includes("nordic") || title.includes("islanda") || title.includes("greenland") || title.includes("antracite") || title.includes("kea") || title.includes("atlantis") || title.includes("fidji")) {
              newTags.add("Sottocategoria:Piscine in acciaio");
          } else if (title.includes("legno") || title.includes("amazonia") || title.includes("mauritius")) {
              newTags.add("Sottocategoria:Piscine in legno");
          } else if (title.includes("composite") || title.includes("avantgarde")) {
              newTags.add("Sottocategoria:Piscine in composito");
          }
      }

      // 2. Filtraggio
      if (title.includes("filtro") || title.includes("pompa") || title.includes("depuratore")) {
          newTags.add("Categoria:Filtraggio");
          if (title.includes("filtro")) newTags.add("Sottocategoria:Filtri");
          if (title.includes("pompa")) newTags.add("Sottocategoria:Pompe per piscine");
      }

      // 3. Pulitori
      if (title.includes("robot") || title.includes("pulitore") || title.includes("aspiratore")) {
          newTags.add("Categoria:Pulitori");
          if (title.includes("robot")) newTags.add("Sottocategoria:Pulitori elettrico");
          else if (title.includes("manuale")) newTags.add("Sottocategoria:Pulitori manuali");
          else newTags.add("Sottocategoria:Pulitori ad aspirazione");
      }

      // 4. Trattamento Acqua (Prodotti Chimici)
      if (title.includes("cloro") || title.includes("bromo") || title.includes("ph ") || title.includes("antialghe")) {
          newTags.add("Categoria:Trattamento acqua");
          newTags.add("Sottocategoria:Prodotti chimici");
      }
      if (title.includes("analisi") || title.includes("tester") || title.includes("blue connect")) {
          newTags.add("Categoria:Trattamento acqua");
          newTags.add("Sottocategoria:Analisi dell'acqua");
      }

      // 5. Coperture
      if (title.includes("copertura") || title.includes("avvolgitore")) {
          newTags.add("Categoria:Coperture");
          if (title.includes("isotermica")) newTags.add("Sottocategoria:Coperture isotermiche");
          else if (title.includes("invernale")) newTags.add("Sottocategoria:Copertura invernale");
          else if (title.includes("avvolgitore")) newTags.add("Sottocategoria:Avvoglitore");
      }

      // 6. Accessori Vari
      if (title.includes("doccia")) { newTags.add("Categoria:Accessori"); newTags.add("Sottocategoria:Docce"); }
      if (title.includes("liner")) { newTags.add("Categoria:Accessori"); newTags.add("Sottocategoria:Liner"); }
      if (title.includes("scaletta") || title.includes("scala")) { newTags.add("Categoria:Accessori"); newTags.add("Sottocategoria:Scalette"); }
      if (title.includes("skimmer")) { newTags.add("Categoria:Accessori"); newTags.add("Sottocategoria:Skimmer"); }
      if (title.includes("tappeto")) { newTags.add("Categoria:Accessori"); newTags.add("Sottocategoria:Tappeti"); }
      if (title.includes("tubo")) { newTags.add("Categoria:Accessori"); newTags.add("Sottocategoria:Tubi"); }

      // 7. Riscaldamento
      if (title.includes("pompa di calore") || title.includes("riscaldamento solare")) {
          newTags.add("Categoria:Riscaldamento");
          if (title.includes("calore")) newTags.add("Sottocategoria:Pompe di calore");
          else newTags.add("Sottocategoria:Riscaldamento solare");
      }

      if (newTags.size > tags.length) {
          await shopifyRequest(`
          mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
              product { id }
              userErrors { message }
            }
          }
          `, {
              input: { id: p.id, tags: Array.from(newTags) }
          });
          updatedCount++;
          if (updatedCount % 20 === 0) console.log(`   ✅ Allineati ${updatedCount} prodotti...`);
      }
  }

  console.log(`\n✅ Allineamento completato. ${updatedCount} prodotti ora popolano correttamente le collezioni.`);
}

alignTagsToCollections().catch(console.error);
