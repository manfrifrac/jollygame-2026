import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function checkDetailedRules() {
    const query = `{
        collection(id: "gid://shopify/Collection/686008336732") {
            title
            ruleSet {
                rules {
                    column
                    relation
                    condition
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
    console.log(JSON.stringify(data.data.collection.ruleSet.rules, null, 2));
}

checkDetailedRules().catch(console.error);
