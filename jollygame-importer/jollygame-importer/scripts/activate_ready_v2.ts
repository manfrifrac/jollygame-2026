import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function activateReadyProducts() {
    console.log("🔍 Ricerca prodotti pronti per l'attivazione (Prezzo > 0)...");

    const query = `
    {
      products(first: 250, query: "status:draft") {
        nodes {
          id
          title
          variants(first: 1) { nodes { price } }
          mediaCount { count }
        }
      }
    }
    `;

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

    let count = 0;
    for (const p of products) {
        const price = parseFloat(p.variants.nodes[0]?.price || "0");
        const hasImages = p.mediaCount.count > 0;

        if (price > 0 && hasImages) {
            console.log(`🚀 Attivazione automatica: ${p.title} (${price} €)`);
            const mutation = `
            mutation {
              productUpdate(input: { id: "${p.id}", status: ACTIVE }) {
                product { id }
                userErrors { message }
              }
            }
            `;
            await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": ACCESS_TOKEN!
                },
                body: JSON.stringify({ query: mutation })
            });
            count++;
        }
    }

    console.log(`\n✅ Operazione completata. ${count} prodotti attivati.`);
}

activateReadyProducts().catch(console.error);
