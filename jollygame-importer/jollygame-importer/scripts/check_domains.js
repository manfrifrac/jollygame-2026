import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `{
    shop {
      primaryDomain {
        url
        host
      }
      domains {
        url
        host
        localization {
          country
        }
      }
    }
  }`;

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query }),
  });

  const result = await response.json();
  console.log("Domain Config:", JSON.stringify(result.data.shop, null, 2));
}

run().catch(console.error);
