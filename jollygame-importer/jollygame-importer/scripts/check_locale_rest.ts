import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function checkLocale() {
  const query = `{
    shop {
      primaryLocale
    }
  }`;
  // Wait, primaryLocale is a field of Shop according to some docs, but it failed earlier.
  // Maybe it's because I used 'primaryLocale' (uppercase L) and it should be 'primaryLocale'? 
  // Wait, I used 'primaryLocale' in check_shop.ts.
  
  // Let's try this instead:
  const query2 = `{
    shop {
      name
    }
  }`;
  // I already did this and it worked.
  
  // Let's try to get all shop locales via REST if GraphQL is being difficult or if I don't know the exact field.
  const restUrl = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/shop.json`;
  const res = await fetch(restUrl, {
    headers: { "X-Shopify-Access-Token": ACCESS_TOKEN! }
  });
  const data = await res.json();
  console.log(JSON.stringify(data.shop.primary_locale, null, 2));
}

checkLocale().catch(console.error);
