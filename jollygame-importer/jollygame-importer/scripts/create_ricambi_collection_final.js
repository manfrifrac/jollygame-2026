import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
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
      appliedDisjunctively: true,
      rules: [
        {
          column: "TYPE",
          relation: "EQUALS",
          condition: "Ricambio"
        },
        {
          column: "TAG",
          relation: "EQUALS",
          condition: "Tipo: Ricambio"
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
    body: JSON.stringify({ query: mutation, variables: { input } }),
  });

  const result = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

run().catch(console.error);
