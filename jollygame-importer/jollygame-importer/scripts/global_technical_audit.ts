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

async function globalTechnicalAudit() {
  console.log("🔍 Avvio Audit Tecnico Globale per tutte le categorie...");

  let hasNextPage = true;
  let cursor = null;
  const auditResults: any[] = [];

  while (hasNextPage) {
    const query = `
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          vendor
          productType
          collections(first: 5) { nodes { title } }
          metafields(first: 30) {
            nodes {
              key
              value
              namespace
            }
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
        const metafields = product.metafields.nodes;
        const findM = (key: string) => metafields.find((f: any) => f.key === key && f.namespace === "custom")?.value || "MISSING";
        
        const category = product.collections.nodes[0]?.title || "Nessuna";
        
        // Definiamo cosa analizzare in base alla categoria
        const technicalData: any = {
            id: product.id,
            title: product.title,
            vendor: product.vendor,
            category: category,
            specs: {}
        };

        if (category.includes("Pulitori")) {
            technicalData.specs = {
                tipo_pulizia: findM("tipo_pulizia"),
                lunghezza_cavo: findM("lunghezza_cavo"),
                filtrazione: findM("filtrazione")
            };
        } else if (category.includes("Piscine")) {
            technicalData.specs = {
                forma: findM("forma"),
                materiale: findM("materiale"),
                volume: findM("volume_acqua"),
                altezza: findM("altezza_vasca")
            };
        } else if (category.includes("Riscaldamento")) {
            technicalData.specs = {
                potenza: findM("potenza_riscaldamento"),
                volume_max: findM("volume_max_piscina"),
                tecnologia: findM("tecnologia_inverter")
            };
        } else if (category.includes("Trattamento")) {
            technicalData.specs = {
                produzione_cloro: findM("produzione_cloro"),
                volume_trattato: findM("volume_acqua")
            };
        }

        auditResults.push(technicalData);
    }
    
    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  // Analisi mancanze
  const summary = {
      total_products: auditResults.length,
      categories: {} as any,
      data_quality: {
          complete: 0,
          partial: 0,
          empty_specs: 0
      }
  };

  auditResults.forEach(p => {
      summary.categories[p.category] = (summary.categories[p.category] || 0) + 1;
      
      const specCount = Object.keys(p.specs).length;
      if (specCount === 0) {
          summary.data_quality.empty_specs++;
      } else {
          const missingCount = Object.values(p.specs).filter(v => v === "MISSING").length;
          if (missingCount === 0) summary.data_quality.complete++;
          else summary.data_quality.partial++;
      }
  });

  console.log("\n📊 STATO DATI TECNICI PER CATEGORIA:");
  console.table(summary.categories);
  
  console.log("\n📉 QUALITÀ SPECIFICHE TECNICHE:");
  console.table(summary.data_quality);

  fs.writeFileSync("global_technical_audit.json", JSON.stringify({ summary, details: auditResults }, null, 2));
  console.log("\n✅ Audit tecnico salvato in 'global_technical_audit.json'");
}

globalTechnicalAudit().catch(console.error);
