import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkSpecificStatus() {
    const titles = ["Piscina Intex Anelli", "Piscina Intex Inflabile", "Piscina Gonfiabile Paradise 6 Persone"];
    
    console.log("🔍 Verifica stato reale su Shopify...");

    for (const title of titles) {
        const query = `{
            products(first: 5, query: "title:'${title}'") {
                nodes {
                    id
                    title
                    status
                    resourcePublicationsV2(first: 5) {
                        nodes {
                            publication { name }
                            isPublished
                        }
                    }
                }
            }
        }`;

        const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": ACCESS_TOKEN!
            },
            body: JSON.stringify({ query })
        });

        const data = await res.json();
        const products = data.data?.products?.nodes || [];

        if (products.length === 0) {
            console.log(`❓ Nessun prodotto trovato con titolo: ${title}`);
        }

        for (const p of products) {
            const isOnline = p.resourcePublicationsV2.nodes.some((pub: any) => 
                pub.publication.name.toLowerCase().includes("online store") && pub.isPublished
            );
            console.log(`📦 ${p.title}`);
            console.log(`   - ID: ${p.id}`);
            console.log(`   - Stato: ${p.status}`);
            console.log(`   - Pubblicato Online: ${isOnline ? "SI 🔴 (ERRORE)" : "NO ✅"}`);
        }
    }
}

checkSpecificStatus().catch(console.error);
