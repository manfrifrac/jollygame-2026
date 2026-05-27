import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `
  mutation collectionCreate($input: CollectionInput!) {
    collectionCreate(input: $input) {
      collection {
        id
        handle
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  const input = {
    title: "Tutti i Ricambi",
    handle: "tutti-i-ricambi",
    ruleSet: {
      appliedDisjunctively: false,
      rules: [
        {
          column: "TYPE",
          relation: "EQUALS",
          condition: "Ricambio"
        }
      ]
    }
  };

  const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query, variables: { input } }),
  });

  const result = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

run().catch(console.error);
