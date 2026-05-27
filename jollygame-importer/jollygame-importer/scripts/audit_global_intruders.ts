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

async function auditAllCategories() {
  console.log("🔍 Avvio Audit Incrociato di tutte le categorie...");

  let hasNextPage = true;
  let cursor = null;
  const allProducts: any[] = [];

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
    allProducts.push(...res.data.products.nodes);
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const intruders: any[] = [];

  const rules = [
    {
      category: "Pulitori",
      tag: "Categoria:Pulitori",
      must_have: ["robot", "pulitore", "aspiratore", "spazzola", "retino", "kit di pulizia", "testa aspirante", "vac", "sweepy", "voyager", "cnx", "alpha", "vortex"],
      must_not_have: ["piscina", "liner", "copertura", "telo", "cloro", "bromo", "antialghe", "svernante", "pompa di calore", "riscaldamento", "filtro", "sabbi"],
      // Eccezione per "Piscina Robot" o "Pulitore per piscina"
      skip_if_starts_with: ["pulitore", "robot", "aspiratore", "kit di pulizia", "spazzola"]
    },
    {
      category: "Trattamento acqua",
      tag: "Categoria:Trattamento acqua",
      must_have: ["cloro", "dicloro", "bromo", "antialghe", "flocculante", "svernante", "alcalinità", "ph", "regolatore", "analizzatore", "tester", "trattamento", "sale", "gel"],
      must_not_have: ["piscina", "robot", "pompa di calore", "telo", "copertura", "scaletta"]
    },
    {
      category: "Filtraggio",
      tag: "Categoria:Filtraggio",
      must_have: ["filtro", "depuratore", "monoblocco", "sabbia", "cartuccia", "pompa", "skimmer", "raccordo"],
      must_not_have: ["pompa di calore", "riscaldamento", "cloro", "bromo", "robot"]
    }
  ];

  for (const product of allProducts) {
    const title = product.title.toLowerCase();
    const tags = product.tags;

    for (const rule of rules) {
        if (tags.includes(rule.tag)) {
            const hasGoodWord = rule.must_have.some(k => title.includes(k));
            const hasBadWord = rule.must_not_have.some(k => title.includes(k));

            let isIntruder = false;
            if (hasBadWord) {
                isIntruder = true;
                // Controlla eccezioni
                if (rule.skip_if_starts_with && rule.skip_if_starts_with.some(k => title.startsWith(k))) {
                    isIntruder = false;
                }
            }

            if (isIntruder) {
                intruders.push({
                    id: product.id,
                    title: product.title,
                    current_category: rule.category,
                    reason: `Trovata keyword sospetta in ${rule.category}`,
                    tags: tags
                });
            }
        }
    }
  }

  console.log(`\n📊 Audit completato.`);
  console.log(`⚠️  Intrusi potenziali trovati: ${intruders.length}`);

  if (intruders.length > 0) {
      console.table(intruders.slice(0, 15).map(i => ({ Prodotto: i.title, Categoria: i.current_category })));
  }

  fs.writeFileSync("global_intruders_audit.json", JSON.stringify(intruders, null, 2));
}

auditAllCategories().catch(console.error);
