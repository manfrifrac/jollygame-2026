import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function testTrackedFalse() {
    const variantId = "gid://shopify/ProductVariant/57298642436444"; // Example variant
    
    console.log("Attempting to get inventoryItemId...");
    
    const getQuery = `{
        productVariant(id: "${variantId}") {
            inventoryItem { id tracked }
        }
    }`;
    
    const resGet = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ query: getQuery })
    });
    
    const dataGet = await resGet.json();
    const invItemId = dataGet.data?.productVariant?.inventoryItem?.id;
    
    if (!invItemId) {
        console.error("Could not find inventoryItemId. Response:", JSON.stringify(dataGet, null, 2));
        return;
    }
    
    console.log(`InventoryItem ID: ${invItemId}`);
    
    const mutation = `
    mutation inventoryItemUpdate($id: ID!, $input: InventoryItemInput!) {
      inventoryItemUpdate(id: $id, input: $input) {
        inventoryItem { id tracked }
        userErrors { field message }
      }
    }
    `;
    
    const resUpdate = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ 
            query: mutation, 
            variables: { id: invItemId, input: { tracked: false } } 
        })
    });
    
    const dataUpdate = await resUpdate.json();
    console.log("Update Result:", JSON.stringify(dataUpdate, null, 2));
}

testTrackedFalse().catch(console.error);
