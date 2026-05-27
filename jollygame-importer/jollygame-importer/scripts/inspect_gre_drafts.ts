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

async function inspectGreDrafts() {
  console.log("🔍 Ispezione specifica prodotti GRE in BOZZA...");

  const query = `
  {
    products(first: 250, query: "status:draft vendor:Gre") {
      nodes {
        id
        title
        handle
        variants(first: 1) { nodes { price sku } }
        metafields(first: 20, namespace: "custom") {
          nodes { key value }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  for (const p of products) {
      const price = parseFloat(p.variants.nodes[0]?.price || "0");
      const sku = p.variants.nodes[0]?.sku;
      const metafields = p.metafields.nodes.map((m: any) => m.key);
      
      console.log(`\n📦 ${p.title}`);
      console.log(`   - Prezzo: ${price} | SKU: ${sku}`);
      console.log(`   - Metafields presenti: ${metafields.join(", ") || "NESSUNO"}`);
      
      // Cerchiamo campi tecnici essenziali per il tema JollyCare
      const essential = ["volume_acqua", "materiale", "dimensioni", "potenza", "portata"];
      const missing = essential.filter(key => !metafields.includes(key));
      
      if (missing.length > 0) {
          console.log(`   ⚠️ Campi tecnici mancanti: ${missing.join(", ")}`);
      }
      
      if (!metafields.includes("lista_ricambi_esploso") && !metafields.includes("ricambi_associati")) {
          console.log(`   ⚠️ Nessun ricambio collegato.`);
      }
  }
}

inspectGreDrafts().catch(console.error);
