import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function finalSyncCheck() {
    const colId = "gid://shopify/Collection/686008336732";
    
    console.log("🔍 Confronto finale Tag vs Contenuto Collezione...");

    // 1. Get products in collection
    const colQuery = `{
        collection(id: "${colId}") {
            products(first: 250) {
                nodes { id title tags }
            }
        }
    }`;
    const resCol = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ query: colQuery })
    });
    const dataCol = await resCol.json();
    const colProducts = dataCol.data?.collection?.products?.nodes || [];

    // 2. Identify discrepancy
    const outliers = colProducts.filter((p: any) => !p.tags.includes("Categoria:Piscine"));

    if (outliers.length > 0) {
        console.log(`⚠️  Discrepanza trovata! ${outliers.length} prodotti sono nella collezione senza avere il tag.`);
        outliers.forEach((p: any) => {
            console.log(`   - ${p.title} (Tags attuali: ${p.tags.join(", ")})`);
        });
        
        console.log("\n🛠️  Tentativo di rimozione forzata (aggiornamento timestamp)...");
        // Often updating a product property forces a collection re-sync
        for (const p of outliers) {
            const mutation = `mutation { productUpdate(input: { id: "${p.id}", note: "re-syncing collection" }) { product { id } } }`;
            await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
                body: JSON.stringify({ query: mutation })
            });
        }
    } else {
        console.log("✅ Nessuna discrepanza. Tutti i prodotti nella collezione hanno il tag corretto.");
    }
}

finalSyncCheck().catch(console.error);
