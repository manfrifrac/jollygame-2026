import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function testInventoryPolicy() {
    const productId = "gid://shopify/Product/15527822393692";
    const variantId = "gid://shopify/ProductVariant/57298642436444";
    
    console.log("Attempting to set inventoryPolicy to CONTINUE...");
    
    const mutation = `
    mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
      productVariantsBulkUpdate(productId: $productId, variants: $variants) {
        product { id }
        productVariants { id inventoryPolicy }
        userErrors { field message }
      }
    }
    `;

    const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": ACCESS_TOKEN!
        },
        body: JSON.stringify({ 
            query: mutation, 
            variables: { 
                productId, 
                variants: [{ id: variantId, inventoryPolicy: "CONTINUE" }] 
            } 
        })
    });

    const data = await res.json();
    console.log("Update Result:", JSON.stringify(data, null, 2));
}

testInventoryPolicy().catch(console.error);
