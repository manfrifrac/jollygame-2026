import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function cleanup() {
  console.log("🔍 Ricerca duplicati per SKU...");
  
  const query = `{
    products(first: 250) {
      nodes {
        id
        title
        handle
        mediaCount { count }
        variants(first: 1) {
          nodes {
            sku
          }
        }
      }
    }
  }`;

  const res = await shopifyRequest(query);
  const products = res.data.products.nodes;
  
  const skuMap: Record<string, any[]> = {};
  const nameMap: Record<string, any[]> = {};

  products.forEach((p: any) => {
    const sku = p.variants.nodes[0]?.sku || "NO-SKU";
    const name = p.title.toLowerCase().trim();
    
    if (sku !== "NO-SKU") {
        if (!skuMap[sku]) skuMap[sku] = [];
        skuMap[sku].push(p);
    } else {
        if (!nameMap[name]) nameMap[name] = [];
        nameMap[name].push(p);
    }
  });

  const toDelete: string[] = [];

  // Analisi per SKU
  for (const sku in skuMap) {
    if (skuMap[sku].length > 1) {
      console.log(`\n👯 Trovati ${skuMap[sku].length} duplicati per SKU: ${sku}`);
      // Ordiniamo: teniamo quello con più immagini
      skuMap[sku].sort((a, b) => b.mediaCount.count - a.mediaCount.count);
      const keep = skuMap[sku][0];
      console.log(`  ✅ Tengo: ${keep.title} (${keep.id}) - Media: ${keep.mediaCount.count}`);
      
      skuMap[sku].slice(1).forEach(p => {
        console.log(`  🗑️ Elimino: ${p.title} (${p.id})`);
        toDelete.push(p.id);
      });
    }
  }

  // Analisi per Nome (per quelli senza SKU)
  for (const name in nameMap) {
    if (nameMap[name].length > 1) {
      console.log(`\n👯 Trovati ${nameMap[name].length} duplicati per Nome: ${name}`);
      nameMap[name].sort((a, b) => b.mediaCount.count - a.mediaCount.count);
      nameMap[name].slice(1).forEach(p => {
        console.log(`  🗑️ Elimino: ${p.title} (${p.id})`);
        toDelete.push(p.id);
      });
    }
  }

  if (toDelete.length > 0) {
    console.log(`\n🚀 Procedo all'eliminazione di ${toDelete.length} prodotti...`);
    for (const id of toDelete) {
      const delMutation = `mutation productDelete($input: ProductDeleteInput!) { productDelete(input: $input) { deletedProductId } }`;
      await shopifyRequest(delMutation, { input: { id } });
      process.stdout.write(".");
    }
    console.log("\n✅ Pulizia completata.");
  } else {
    console.log("\n✨ Nessun duplicato trovato.");
  }
}

cleanup().catch(console.error);
