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

async function smartCategorization() {
  console.log("🧠 Avvio Categorizzazione Smart dei Prodotti...");

  // 1. Mappa Collezioni
  const colRes = await shopifyRequest(`{ collections(first: 250) { nodes { id title handle } } }`);
  const colMap: Record<string, string> = {};
  colRes.data.collections.nodes.forEach((c: any) => { colMap[c.handle] = c.id; });

  const cats = {
      ACCIAIO: colMap["piscine-in-acciaio"],
      LEGNO: colMap["piscine-in-legno"],
      COMPOSITO: colMap["piscine-in-composito"],
      FUORI_TERRA: colMap["piscine-fuori-terra"],
      ROBOT: colMap["pulitori-elettrico"],
      MANUALI: colMap["pulitori-manuali"],
      ASPIRAZIONE: colMap["pulitori-ad-aspirazione"],
      PULITORI: colMap["pulitori"],
      POMPE_CALORE: colMap["pompe-di-calore"],
      RISCALDAMENTO: colMap["riscaldamento"],
      CHIMICI: colMap["prodotti-chimici"],
      TRATTAMENTO: colMap["trattamento-acqua"],
      FILTRI: colMap["filtri"],
      FILTRAGGIO: colMap["filtraggio"],
      POMPE: colMap["pompe-per-piscine"],
      COPERTURE: colMap["coperture"],
      COPERTURA_INV: colMap["copertura-invernale"],
      LINER: colMap["liner-e-riparatori"],
      LUCI: colMap["illuminazione"],
      ACCESSORI: colMap["accessori"],
      ALTRI_ACC: colMap["altri-accessori"],
      TUBI: colMap["tubi"],
      INTERRATE: colMap["piscine-interrate"],
      RICAMBI: colMap["tutti-i-ricambi"]
  };

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
          handle
          productType
          collections(first: 20) { nodes { handle } }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const title = product.title.toLowerCase();
      const type = (product.productType || "").toLowerCase();
      const currentCollections = product.collections.nodes.map((c: any) => c.handle);
      const toJoin: string[] = [];

      // --- LOGICA DI CATEGORIZZAZIONE ---

      // 1. PISCINE IN ACCIAIO
      if (title.includes("acciaio") || ["pacific", "sicilia", "fidji", "bora bora", "haiti", "atlantis", "steel", "metallica", "mauritius", "varadero", "granada"].some(k => title.includes(k))) {
          if (product.vendor === 'Gre' || product.vendor === 'Intex' || product.vendor === 'Bestway') {
              if (cats.ACCIAIO) toJoin.push(cats.ACCIAIO);
              if (cats.FUORI_TERRA) toJoin.push(cats.FUORI_TERRA);
          }
      }

      // 2. PISCINE IN LEGNO
      if (title.includes("legno") || ["lili", "grenade", "marbella", "vermela", "city", "mint", "violette", "cardamon", "safran", "cannelle", "carra", "vanille"].some(k => title.includes(k))) {
          if (product.vendor === 'Gre') {
              if (cats.LEGNO) toJoin.push(cats.LEGNO);
              if (cats.FUORI_TERRA) toJoin.push(cats.FUORI_TERRA);
          }
      }

      // 3. PISCINE IN COMPOSITO
      if (title.includes("composito") || title.includes("composite") || title.includes("avantgarde")) {
          if (cats.COMPOSITO) toJoin.push(cats.COMPOSITO);
          if (cats.FUORI_TERRA) toJoin.push(cats.FUORI_TERRA);
      }

      // 4. PULITORI ELETTRICI (ROBOT)
      if (title.includes("robot") || title.includes("pulitore elettrico") || ["oa ", "ra ", "swy", "cnx", "voyager", "alpha", "sweepy", "vortex"].some(k => title.includes(k))) {
          if (cats.ROBOT) toJoin.push(cats.ROBOT);
          if (cats.PULITORI) toJoin.push(cats.PULITORI);
      }

      // 5. PULITORI MANUALI
      if (title.includes("manuale") || title.includes("spazzola") || title.includes("retino") || title.includes("kit di pulizia") || title.includes("aspiratore elettronico") || title.includes("testa aspirante")) {
          if (cats.MANUALI) toJoin.push(cats.MANUALI);
          if (cats.PULITORI) toJoin.push(cats.PULITORI);
      }

      // 6. PULITORI AD ASPIRAZIONE (IDRAULICI)
      if (title.includes("idraulico") || title.includes("silence vac")) {
          if (cats.ASPIRAZIONE) toJoin.push(cats.ASPIRAZIONE);
          if (cats.PULITORI) toJoin.push(cats.PULITORI);
      }

      // 7. POMPE DI CALORE
      if (title.includes("pompa di calore") || ["z250", "z350", "z400", "z550", "z650", "inverter"].some(k => title.includes(k))) {
          if (cats.POMPE_CALORE) toJoin.push(cats.POMPE_CALORE);
          if (cats.RISCALDAMENTO) toJoin.push(cats.RISCALDAMENTO);
      }

      // 8. CHIMICI
      if (["cloro", "dicloro", "bromo", "antialghe", "flocculante", "svernante", "alcalinità", " ph", "regolatore", "analizzatore", "tester"].some(k => title.includes(k))) {
          if (cats.CHIMICI) toJoin.push(cats.CHIMICI);
          if (cats.TRATTAMENTO) toJoin.push(cats.TRATTAMENTO);
      }

      // 9. FILTRI
      if (title.includes("filtro") || title.includes("depuratore") || title.includes("monoblocco") || title.includes("sabbia") || title.includes("cartuccia filtrante")) {
          // Escludiamo le pompe di calore che potrebbero avere la parola filtro nel testo
          if (!title.includes("calore")) {
              if (cats.FILTRI) toJoin.push(cats.FILTRI);
              if (cats.FILTRAGGIO) toJoin.push(cats.FILTRAGGIO);
          }
      }

      // 10. COPERTURE
      if (title.includes("copertura") || title.includes("telo") || title.includes("copertore")) {
          if (cats.COPERTURE) toJoin.push(cats.COPERTURE);
          if (title.includes("invernale")) {
              if (cats.COPERTURA_INV) toJoin.push(cats.COPERTURA_INV);
          }
          if (title.includes("isotermica") || title.includes("termico") || title.includes("bolle")) {
              if (colMap["coperture-isotermiche"]) toJoin.push(colMap["coperture-isotermiche"]);
          }
      }

      // 11. LINER
      if (title.includes("liner") || title.includes("riparazione")) {
          if (cats.LINER) toJoin.push(cats.LINER);
      }

      // 12. ILLUMINAZIONE
      if (title.includes("led") || title.includes("proiettore") || title.includes("faro") || title.includes("lampada")) {
          if (cats.LUCI) toJoin.push(cats.LUCI);
      }

      // 13. ACCESSORI TECNICI / TUBI
      if (title.includes("raccordo") || title.includes("manico") || title.includes("termometro") || title.includes("erogatore") || title.includes("adesivo") || title.includes("plug") || title.includes("casetta")) {
          if (cats.ACCESSORI) toJoin.push(cats.ACCESSORI);
          if (cats.ALTRI_ACC) toJoin.push(cats.ALTRI_ACC);
      }
      if (title.includes("tubo")) {
          if (cats.TUBI) toJoin.push(cats.TUBI);
          if (cats.ACCESSORI) toJoin.push(cats.ACCESSORI);
      }

      // 14. RICAMBI (Se marcati come tali nel tipo o vendor)
      if (type.includes("ricambio") || type.includes("spare part")) {
          if (cats.RICAMBI) toJoin.push(cats.RICAMBI);
      }

      // --- ESECUZIONE AGGIORNAMENTO ---
      // Filtriamo quelli che sono già presenti
      const uniqueToJoin = [...new Set(toJoin)].filter(id => {
          // Cerchiamo l'handle corrispondente all'ID
          const handle = Object.keys(colMap).find(h => colMap[h] === id);
          return !currentCollections.includes(handle || "");
      });

      if (uniqueToJoin.length > 0) {
        console.log(`🏷️  Assegnazione: ${product.title} -> [${uniqueToJoin.length} nuove collezioni]`);
        const mutation = `
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product { id }
            userErrors { message }
          }
        }
        `;
        const updateRes = await shopifyRequest(mutation, {
            input: {
                id: product.id,
                collectionsToJoin: uniqueToJoin
            }
        });
        if (updateRes.data?.productUpdate?.product) {
            totalUpdated++;
        } else {
            console.error(`❌ Errore aggiornamento ${product.title}:`, updateRes.data?.productUpdate?.userErrors);
        }
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log(`\n\n✅ Categorizzazione completata. Aggiornati ${totalUpdated} prodotti.`);
}

smartCategorization().catch(console.error);
