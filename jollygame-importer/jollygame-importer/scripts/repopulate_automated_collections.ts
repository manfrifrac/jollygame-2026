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

async function repopulateAutomated() {
  console.log("🛠️  Ricaricamento Categorizzazione via Tag Esatti...");

  let hasNextPage = true;
  let cursor = null;
  let totalUpdated = 0;

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
          tags
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const title = product.title.toLowerCase();
      const currentTags = product.tags;
      const newTags = new Set(currentTags);
      
      // 1. PISCINE
      if (title.includes("piscina") || ["pacific", "sicilia", "fidji", "bora bora", "haiti", "atlantis", "steel", "metallica", "mauritius", "varadero", "granada", "lili", "grenade", "marbella", "vermela", "city", "mint", "avantgarde", "easy set", "prisma"].some(k => title.includes(k))) {
          newTags.add("Categoria:Piscine");
          
          if (title.includes("acciaio") || ["pacific", "sicilia", "fidji", "bora bora", "haiti", "atlantis", "steel", "metallica", "mauritius", "varadero", "granada", "power steel", "metallica"].some(k => title.includes(k))) {
              newTags.add("Sottocategoria:Piscine in acciaio");
          } else if (title.includes("legno") || ["lili", "grenade", "marbella", "vermela", "city", "mint", "violette", "cardamon", "safran", "cannelle", "carra", "vanille"].some(k => title.includes(k))) {
              newTags.add("Sottocategoria:Piscine in legno");
          } else if (title.includes("composito") || title.includes("composite") || title.includes("avantgarde")) {
              newTags.add("Sottocategoria:Piscine in composito");
          } else if (title.includes("interrata") || title.includes("interrate")) {
              newTags.add("Sottocategoria:Piscine interrate");
          }
      }

      // 2. PULITORI
      if (title.includes("pulitore") || title.includes("robot") || title.includes("aspiratore") || title.includes("spazzola") || title.includes("retino") || ["oa ", "ra ", "swy", "cnx", "voyager", "alpha", "sweepy", "vortex"].some(k => title.includes(k))) {
          newTags.add("Categoria:Pulitori");
          
          if (title.includes("robot") || title.includes("elettrico") || ["oa ", "ra ", "swy", "cnx", "voyager", "alpha", "sweepy", "vortex"].some(k => title.includes(k))) {
              newTags.add("Sottocategoria:Pulitori elettrico");
          } else if (title.includes("manuale") || title.includes("spazzola") || title.includes("retino") || title.includes("kit di pulizia") || title.includes("testa aspirante")) {
              newTags.add("Sottocategoria:Pulitori manuali");
          } else if (title.includes("idraulico") || title.includes("silence vac")) {
              newTags.add("Sottocategoria:Pulitori ad aspirazione");
          }
      }

      // 3. FILTRAGGIO
      if (title.includes("filtro") || title.includes("depuratore") || title.includes("monoblocco") || title.includes("sabbia") || title.includes("cartuccia filtrante") || title.includes("pompa")) {
          if (!title.includes("calore")) {
              newTags.add("Categoria:Filtraggio");
              if (title.includes("pompa") || title.includes("flo pro") || title.includes("flopro") || title.includes("autoadescante")) {
                  newTags.add("Sottocategoria:Pompe per piscine");
              } else {
                  newTags.add("Sottocategoria:Filtri");
              }
          }
      }

      // 4. TRATTAMENTO ACQUA
      if (["cloro", "dicloro", "bromo", "antialghe", "flocculante", "svernante", "alcalinità", " ph", "regolatore", "analizzatore", "tester", "trattamento"].some(k => title.includes(k))) {
          newTags.add("Categoria:Trattamento acqua");
          newTags.add("Sottocategoria:Prodotti chimici");
      }

      // 5. RISCALDAMENTO
      if (title.includes("pompa di calore") || title.includes("riscaldamento") || ["z250", "z350", "z400", "z550", "z650", "inverter", "force inverter"].some(k => title.includes(k))) {
          newTags.add("Categoria:Riscaldamento");
          if (title.includes("pompa") || title.includes("inverter")) {
              newTags.add("Sottocategoria:Pompe di calore");
          } else {
              newTags.add("Sottocategoria:Riscaldamento solare");
          }
      }

      // 6. COPERTURE
      if (title.includes("copertura") || title.includes("telo") || title.includes("copertore")) {
          newTags.add("Categoria:Coperture");
          if (title.includes("invernale")) {
              newTags.add("Sottocategoria:Copertura invernale");
          } else if (title.includes("isotermica") || title.includes("termico") || title.includes("bolle")) {
              newTags.add("Sottocategoria:Coperture isotermiche");
          }
      }

      // 7. ALTRO
      if (title.includes("liner") || title.includes("riparazione")) {
          newTags.add("Sottocategoria:Liner e riparatori");
      }
      if (title.includes("led") || title.includes("proiettore") || title.includes("faro") || title.includes("lampada")) {
          newTags.add("Sottocategoria:Illuminazione");
      }
      if (title.includes("raccordo") || title.includes("manico") || title.includes("termometro") || title.includes("erogatore") || title.includes("adesivo") || title.includes("plug") || title.includes("casetta") || title.includes("tubo")) {
          newTags.add("Categoria:Accessori");
          newTags.add("Sottocategoria:Altri accessori");
      }

      // Speciale Intex/Bestway se non classificati
      if (product.vendor === "Intex" || product.vendor === "Bestway") {
          if (title.includes("piscina")) newTags.add("Categoria:Piscine");
          if (title.includes("telo") || title.includes("copri")) newTags.add("Categoria:Coperture");
          if (title.includes("pompa")) newTags.add("Categoria:Filtraggio");
      }

      if (newTags.size !== currentTags.length) {
          const finalTags = Array.from(newTags);
          const mutation = `mutation productUpdate($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`;
          await shopifyRequest(mutation, { input: { id: product.id, tags: finalTags } });
          totalUpdated++;
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`✅ Aggiornati ${totalUpdated} prodotti.`);
}

repopulateAutomated().catch(console.error);
