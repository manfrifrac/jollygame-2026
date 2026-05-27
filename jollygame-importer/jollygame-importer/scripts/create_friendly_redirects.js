import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const redirects = [
    { path: "/ricambi-zodiac", target: "/a/metaobjects/brand_ricambi/zodiac" },
    { path: "/ricambi-intex", target: "/a/metaobjects/brand_ricambi/intex" },
    { path: "/ricambi-bestway", target: "/a/metaobjects/brand_ricambi/bestway" },
    { path: "/ricambi-gre", target: "/a/metaobjects/brand_ricambi/gre" }
  ];

  const mutation = `
  mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
    urlRedirectCreate(urlRedirect: $urlRedirect) {
      urlRedirect {
        id
        path
        target
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  for (const redir of redirects) {
    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ 
        query: mutation, 
        variables: { 
          urlRedirect: {
            path: redir.path,
            target: redir.target
          }
        } 
      }),
    });

    const result = await response.json();
    console.log(`Redirect ${redir.path} result:`, JSON.stringify(result, null, 2));
  }
}

run().catch(console.error);
