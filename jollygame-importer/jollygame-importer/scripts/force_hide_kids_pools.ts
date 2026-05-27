import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function forceDraftAndHide() {
    const idsToHide = [
        "gid://shopify/Product/15591518863708", // Anelli
        "gid://shopify/Product/15591518732636", // Inflabile
        "gid://shopify/Product/15591518568796", // Cani
        "gid://shopify/Product/15591519289692"  // Paradise
    ];

    console.log("🛡️ Esecuzione FORCE HIDE per piscine non desiderate...");

    // 1. Recuperiamo ID pubblicazione Online Store per sicurezza (per toglierlo dai canali)
    const pubRes = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ query: `{ publications(first: 10) { nodes { id name } } }` })
    });
    const pubData = await pubRes.json();
    const onlineStoreId = pubData.data?.publications?.nodes.find((n: any) => n.name.toLowerCase().includes("online store"))?.id;

    for (const id of idsToHide) {
        console.log(`\n📦 Nascondendo ID: ${id}`);
        
        // A. Spostamento in BOZZA
        const updateMutation = `
        mutation {
          productUpdate(input: { id: "${id}", status: DRAFT }) {
            product { title status }
            userErrors { message }
          }
        }
        `;
        
        const resUpdate = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
            body: JSON.stringify({ query: updateMutation })
        });
        const dataUpdate = await resUpdate.json();
        
        if (dataUpdate.data?.productUpdate?.product) {
            console.log(`   ✅ Stato cambiato in: ${dataUpdate.data.productUpdate.product.status}`);
        } else {
            console.log(`   ❌ Errore cambio stato:`, dataUpdate.data?.productUpdate?.userErrors);
        }

        // B. Rimozione da Online Store (De-publication)
        if (onlineStoreId) {
            const unpublishMutation = `
            mutation {
              publishableUnpublish(id: "${id}", input: { publicationId: "${onlineStoreId}" }) {
                userErrors { message }
              }
            }
            `;
            await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
                body: JSON.stringify({ query: unpublishMutation })
            });
            console.log(`   ✅ Rimosso da Online Store.`);
        }
    }

    console.log("\n🚀 Operazione completata. I prodotti sono ora invisibili.");
}

forceDraftAndHide().catch(console.error);
