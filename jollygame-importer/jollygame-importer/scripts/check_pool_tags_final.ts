import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkPoolTaggedProducts() {
    const query = `{
        products(first: 250, query: "tag:'Categoria:Piscine'") {
            nodes {
                title
                status
            }
        }
    }`;
    const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ query })
    });
    const data = await res.json();
    const products = data.data?.products?.nodes || [];
    console.log(`\n📦 Prodotti con tag "Categoria:Piscine" (${products.length}):`);
    products.forEach((p: any) => console.log(` - ${p.title} [${p.status}]`));
}

checkPoolTaggedProducts().catch(console.error);
