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

async function surgicalCleanup() {
  console.log("🧼 Inizio pulizia chirurgica dei duplicati...");
  
  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        variants(first: 1) {
          nodes {
            sku
          }
        }
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  const products: any[] = [];

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    products.push(...res.data.products.nodes);
    hasNext = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  const nameMap: Record<string, any[]> = {};
  products.forEach(p => {
    const name = p.title.toLowerCase().trim();
    if (!nameMap[name]) nameMap[name] = [];
    nameMap[name].push(p);
  });

  const toDelete: string[] = [];

  for (const name in nameMap) {
    const instances = nameMap[name];
    if (instances.length > 1) {
      // Regola 1: Se una istanza ha lo SKU e l'altra no, elimina quella senza SKU
      const withSku = instances.filter(i => i.variants.nodes[0]?.sku);
      const withoutSku = instances.filter(i => !i.variants.nodes[0]?.sku);

      if (withSku.length > 0 && withoutSku.length > 0) {
        console.log(`👯 [${instances[0].title}] Trovate versioni con e senza SKU. Elimino quelle senza.`);
        withoutSku.forEach(i => toDelete.push(i.id));
      } 
      // Regola 2: Se hanno entrambi SKU null, tieni solo il primo (il più vecchio solitamente nel fetch)
      else if (withSku.length === 0) {
        console.log(`👯 [${instances[0].title}] Tutte senza SKU. Tengo solo la prima.`);
        instances.slice(1).forEach(i => toDelete.push(i.id));
      }
      // Nota: Se hanno SKU diversi ma stesso nome, le lasciamo (sono modelli diversi come Anthracite)
    }
  }

  console.log(`\n🚀 Eliminazione di ${toDelete.length} duplicati...`);
  for (const id of toDelete) {
    const delMutation = `mutation productDelete($input: ProductDeleteInput!) { productDelete(input: $input) { deletedProductId } }`;
    await shopifyRequest(delMutation, { input: { id } });
    process.stdout.write(".");
  }
  console.log("\n✅ Pulizia chirurgica completata.");
}

surgicalCleanup().catch(console.error);
