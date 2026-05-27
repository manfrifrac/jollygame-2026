import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function stripPoolTagFromDrafts() {
    const ids = [
        "gid://shopify/Product/15591518863708", // Anelli
        "gid://shopify/Product/15591518732636", // Inflabile
        "gid://shopify/Product/15591518568796", // Cani
        "gid://shopify/Product/15591519289692"  // Paradise
    ];

    console.log("🛡️ RIMOZIONE TAG PISCINA DA PRODOTTI DRAFT...");

    for (const id of ids) {
        const getQuery = `{ product(id: "${id}") { tags } }`;
        const resGet = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
            body: JSON.stringify({ query: getQuery })
        });
        const dataGet = await resGet.json();
        const currentTags = dataGet.data?.product?.tags || [];

        const newTags = currentTags.filter((t: string) => t !== "Categoria:Piscine");

        const mutation = `
        mutation {
          productUpdate(input: { id: "${id}", tags: ${JSON.stringify(newTags)} }) {
            product { title tags }
          }
        }
        `;
        await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
            body: JSON.stringify({ query: mutation })
        });
        console.log(`   ✅ Tag rimosso per ID: ${id}`);
    }
}

stripPoolTagFromDrafts().catch(console.error);
