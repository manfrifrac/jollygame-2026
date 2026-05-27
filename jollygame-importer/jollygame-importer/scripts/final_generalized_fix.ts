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

const FINAL_DRAFTS = [
    "gid://shopify/Product/15527774421340",
    "gid://shopify/Product/15527820099932",
    "gid://shopify/Product/15527820165468",
    "gid://shopify/Product/15527830978908"
];

async function finalFix() {
    console.log("🛠️ Ultime correzioni: Stato Bozza per prodotti rimasti a prezzo 0...");
    for (const id of FINAL_DRAFTS) {
        await shopifyRequest(`mutation { productUpdate(input: { id: "${id}", status: DRAFT }) { product { id } userErrors { message } } }`);
        console.log(`✅ ${id} -> DRAFT`);
    }

    console.log("\n🧹 Pulizia descrizioni specifica...");
    const productsToClean = [
        { id: "gid://shopify/Product/15591516832092", title: "Robot Pulitore Automatico" },
        { id: "gid://shopify/Product/15546245611868", title: "FloPro™ VS" },
        { id: "gid://shopify/Product/15546245710172", title: "Z350iQ" }
    ];

    for (const p of productsToClean) {
        // Recupera la descrizione attuale
        const res = await shopifyRequest(`{ product(id: "${p.id}") { descriptionHtml } }`);
        const currentHtml = res.data?.product?.descriptionHtml;
        if (currentHtml) {
            // Rimuove leakage AI
            let cleaned = currentHtml.replace(/Ecco una descrizione ottimizzata:?/gi, "")
                                   .replace(/Nuovo titolo:.*$/gim, "")
                                   .replace(/Rispondi solo con.*$/gim, "")
                                   .replace(/Sei un esperto di copywriting.*$/gim, "");
            
            await shopifyRequest(`mutation { productUpdate(input: { id: "${p.id}", descriptionHtml: """${cleaned.trim()}""" }) { product { id } } }`);
            console.log(`✅ Descrizione pulita per: ${p.title}`);
        }
    }
    
    console.log("\n🎉 Tutte le correzioni critiche completate.");
}

finalFix().catch(console.error);
