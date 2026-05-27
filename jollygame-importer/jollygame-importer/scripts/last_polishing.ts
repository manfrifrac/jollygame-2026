import dotenv from "dotenv";

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

async function lastPolishing() {
    console.log("✨ Ultimi ritocchi qualitativi...");

    // 1. Sposta in bozza Bestway senza immagini
    const bestwayId = "gid://shopify/Product/15591520272732";
    await shopifyRequest(`mutation { productUpdate(input: { id: "${bestwayId}", status: DRAFT }) { product { id } } }`);
    console.log("✅ Spostata in bozza: Piscina Bestway Solo Struttura (mancano immagini)");

    // 2. Correzione titolo francese
    const search = await shopifyRequest(`{ 
      products(first: 250, query: "handle:gonfiabile-piscina-a-shaped-paradise-6-personne-intex-iprs300f-01") { 
        nodes { id title } 
      } 
    }`);
    const target = search.data?.products?.nodes[0];
    
    if (target) {
        const newTitle = "Piscina Gonfiabile Paradise 6 Persone - Intex IPRS300F-01";
        await shopifyRequest(`mutation { productUpdate(input: { id: "${target.id}", title: "${newTitle}" }) { product { id } } }`);
        console.log(`✅ Titolo tradotto: "${target.title}" -> "${newTitle}"`);
    } else {
        console.log("ℹ️ Prodotto francese non trovato via handle.");
    }

    console.log("\n🚀 Catalogo online ottimizzato e pulito.");
}

lastPolishing().catch(console.error);
