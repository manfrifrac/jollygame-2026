import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `{
    metaobjectDefinitions(first: 50) {
      nodes {
        id
        type
        name
        capabilities {
          publishable {
            enabled
          }
        }
      }
    }
    metaobjects(first: 5, type: "documento_tecnico") {
      nodes {
        id
        handle
        fields {
          key
          value
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
  console.log(JSON.stringify(result, null, 2));
}

run().catch(console.error);
