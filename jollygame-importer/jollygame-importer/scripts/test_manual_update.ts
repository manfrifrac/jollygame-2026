import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function testUpdate() {
    const productId = "gid://shopify/Product/15527770587484";
    const variantId = "gid://shopify/ProductVariant/57298392219996";
    const price = "2.85";

    console.log("Testing update for 40009...");

    const mutation = `
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product { id status variants(first:1) { nodes { price } } }
        userErrors { field message }
      }
    }
    `;

    const input = {
        id: productId,
        status: "ACTIVE",
        variants: [
            {
                id: variantId,
                price: price
            }
        ]
    };

    const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": ACCESS_TOKEN!
        },
        body: JSON.stringify({ query: mutation, variables: { input } })
    });

    const data = await res.json();
    console.log(JSON.stringify(data, null, 2));
}

testUpdate().catch(console.error);
