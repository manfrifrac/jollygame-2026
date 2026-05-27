import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const MO_ID = "gid://shopify/Metaobject/532151697756";
  const PRODUCT_ID = "gid://shopify/Product/15546245513564"; // cnx-50-iq

  console.log("1. Publishing Metaobject...");
  const publishMutation = `
  mutation metaobjectUpdate($id: ID!, $metaobject: MetaobjectUpdateInput!) {
    metaobjectUpdate(id: $id, metaobject: $metaobject) {
      metaobject { id }
      userErrors { field message }
    }
  }
  `;

  // Note: in 2024-10, status might be part of the metaobject update or a separate capability mutation.
  // Actually, standard metaobjectUpdate handles capabilities too.
  
  const publishRes = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ 
      query: publishMutation, 
      variables: { 
        id: MO_ID, 
        metaobject: { 
          capabilities: { 
            publishable: { status: "ACTIVE" } 
          } 
        } 
      } 
    }),
  });

  const publishResult = await publishRes.json();
  console.log("Publish Result:", JSON.stringify(publishResult, null, 2));

  console.log("2. Associating Metaobject to Product cnx-50-iq...");
  const associateMutation = `
  mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
      product { id }
      userErrors { field message }
    }
  }
  `;

  const associateInput = {
    id: PRODUCT_ID,
    metafields: [
      {
        namespace: "custom",
        key: "ricambi_compatibili",
        value: JSON.stringify([MO_ID])
      }
    ]
  };

  const associateRes = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: associateMutation, variables: { input: associateInput } }),
  });

  const associateResult = await associateRes.json();
  console.log("Associate Result:", JSON.stringify(associateResult, null, 2));
}

run().catch(console.error);
