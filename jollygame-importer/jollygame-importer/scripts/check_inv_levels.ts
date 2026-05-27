import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkInventoryLevels() {
    const variantId = "gid://shopify/ProductVariant/57298642436444";
    
    console.log("Fetching inventory levels for variant...");
    
    const query = `{
        productVariant(id: "${variantId}") {
            title
            inventoryItem {
                id
                inventoryLevels(first: 5) {
                    nodes {
                        id
                        quantities(names: ["available"]) {
                            name
                            quantity
                        }
                        location {
                            id
                            name
                        }
                    }
                }
            }
        }
    }`;
    
    const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
        body: JSON.stringify({ query })
    });
    
    const data = await res.json();
    console.log(JSON.stringify(data, null, 2));
}

checkInventoryLevels().catch(console.error);
