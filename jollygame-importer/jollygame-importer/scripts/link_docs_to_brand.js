import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const query = `{
    zodiac: metaobjectByHandle(handle: { handle: "zodiac", type: "brand_ricambi" }) { id }
    docs: metaobjects(first: 50, type: "documento_tecnico") {
      nodes {
        id
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
  const zodiacId = result.data.zodiac.id;
  const docs = result.data.docs.nodes;

  const zodiacDocs = docs.filter(d => 
    d.fields.some(f => f.key === "titolo" && (f.value.includes("RA ") || f.value.includes("OA ") || f.value.includes("Zodiac") || f.value.includes("ALPHA iQ")))
  ).map(d => d.id);

  console.log(`Linking ${zodiacDocs.length} documents to Zodiac.`);

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

  const metaobject = {
    fields: [
      { key: "documentazione", value: JSON.stringify(zodiacDocs) }
    ]
  };

  const updateResponse = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query: mutation, variables: { id: zodiacId, metaobject } }),
  });

  const updateResult = await updateResponse.json();
  console.log("Zodiac Link Result:", JSON.stringify(updateResult, null, 2));
}

run().catch(console.error);
