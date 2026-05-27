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

async function smartCategorize() {
  const data = JSON.parse(fs.readFileSync("master_catalog_dump.json", "utf8"));
  const greProducts = data.filter((p: any) => p.vendor === "Gre");

  console.log(`🔍 Analisi di ${greProducts.length} prodotti Gre per categorizzazione...`);

  let updatedCount = 0;

  for (const p of greProducts) {
      // Se è una serie consolidata, ha già i tag giusti, ma facciamo un refresh se necessario
      const title = p.title.toLowerCase();
      const tags: string[] = p.tags || [];
      const newTags = new Set(tags);

      // Logica di Categorizzazione
      let category = "";
      let subcategory = "";

      if (title.includes("piscina gre serie") || title.includes("kit piscina")) {
          category = "Piscine";
          subcategory = title.includes("ovale") ? "Ovali" : title.includes("tonda") ? "Tonde" : "Rettangolari";
      } else if (title.includes("cloro") || title.includes("bromo") || title.includes("ph") || title.includes("antialghe") || title.includes("flocculante") || title.includes("ossigeno") || title.includes("pastiglie") || title.includes("granulare")) {
          category = "Prodotti Chimici";
          subcategory = title.includes("pastiglie") ? "In Pastiglie" : title.includes("granulare") ? "Granulari" : "Liquidi";
      } else if (title.includes("copertura") || title.includes("avvolgitore")) {
          category = "Coperture";
          subcategory = title.includes("isotermica") ? "Isotermiche (Estate)" : title.includes("invernale") ? "Invernali" : "Accessori Coperture";
      } else if (title.includes("robot") || title.includes("pulitore") || title.includes("aspiratore") || title.includes("spazzola") || title.includes("retino") || title.includes("raccoglitore")) {
          category = "Robot e Pulizia";
          subcategory = title.includes("robot") ? "Robot Automatici" : title.includes("pulitore") ? "Pulitori Manuali/Idraulici" : "Accessori Pulizia";
      } else if (title.includes("liner")) {
          category = "Liner";
          subcategory = title.includes("ovale") ? "Liner Ovali" : title.includes("tonda") ? "Liner Tondi" : "Liner Rettangolari";
      } else if (title.includes("doccia") || title.includes("lavapiedi")) {
          category = "Docce";
          subcategory = "Docce da Esterno";
      } else if (title.includes("skimmer") || title.includes("valvola") || title.includes("raccordo") || title.includes("filtro") || title.includes("pompa") || title.includes("manometro")) {
          category = "Ricambi e Componenti";
          subcategory = title.includes("filtro") || title.includes("pompa") ? "Filtrazione" : "Pezzi di Ricambio";
      } else if (title.includes("analisi") || title.includes("tester") || title.includes("blue connect") || title.includes("strisce")) {
          category = "Analisi Acqua";
          subcategory = "Strumenti di Misura";
      }

      if (category) {
          newTags.add(`Categoria:${category}`);
          if (subcategory) newTags.add(`Sottocategoria:${subcategory}`);
          
          // Se i tag sono cambiati, aggiorna
          if (newTags.size > tags.length) {
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
                      id: p.id,
                      tags: Array.from(newTags)
                  }
              });
              updatedCount++;
              if (updatedCount % 20 === 0) console.log(`   ✅ Categorizzati ${updatedCount} prodotti...`);
          }
      }
  }

  console.log(`\n✅ Operazione completata. ${updatedCount} prodotti sono stati assegnati alle loro categorie.`);
}

smartCategorize().catch(console.error);
