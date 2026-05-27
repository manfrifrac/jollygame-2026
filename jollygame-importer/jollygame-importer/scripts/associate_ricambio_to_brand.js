import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

async function run() {
  const mutation = `
  mutation metaobjectUpdate($id: ID!, $metaobject: MetaobjectUpdateInput!) {
    metaobjectUpdate(id: $id, metaobject: $metaobject) {
      metaobject {
        id
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  // ID del metaobject "Zodiac" di tipo brand_ricambi
  const brandMetaobjectId = "gid://shopify/Metaobject/531234750812"; 

  // ID del metaobject "VITE 4*12 MM (*5)" di tipo ricambio
  const ricambioMetaobjectId = "gid://shopify/Metaobject/532151697756";

  const updateResponse = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN },
    body: JSON.stringify({ 
      query: mutation, 
      variables: { 
        id: brandMetaobjectId,
        metaobject: {
          fields: [
            {
              key: "ricambi_associati",
              value: JSON.stringify([ricambioMetaobjectId])
            }
          ]
        }
      } 
    }),
  });

  const updateResult = await updateResponse.json();
  console.log("Result:", JSON.stringify(updateResult, null, 2));
}

run().catch(console.error);
