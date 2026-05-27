import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `{
    urlRedirects(first: 10, query: "path:/ricambi-") {
      nodes {
        id
        path
        target
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
  const nodes = result.data.urlRedirects.nodes;
  
  const mutation = `
  mutation urlRedirectUpdate($id: ID!, $urlRedirect: UrlRedirectInput!) {
    urlRedirectUpdate(id: $id, urlRedirect: $urlRedirect) {
      urlRedirect {
        id
        target
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  for (const node of nodes) {
    const brand = node.path.replace("/ricambi-", "");
    const newTarget = `/pages/brand-ricambi/${brand}`;
    
    const updateResponse = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ 
        query: mutation, 
        variables: { 
          id: node.id,
          urlRedirect: { target: newTarget }
        } 
      }),
    });

    const updateResult = await updateResponse.json();
    console.log(`Updated ${node.path} to ${newTarget}:`, JSON.stringify(updateResult, null, 2));
  }
}

run().catch(console.error);
