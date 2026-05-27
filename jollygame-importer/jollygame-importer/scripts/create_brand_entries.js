import dotenv from 'dotenv';
dotenv.config();

async function run() {
  const mutation = `
  mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
    metaobjectCreate(metaobject: $metaobject) {
      metaobject {
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

  const brands = [
    { name: "Zodiac", handle: "zodiac" },
    { name: "Intex", handle: "intex" },
    { name: "Bestway", handle: "bestway" },
    { name: "Gre", handle: "gre" }
  ];

  for (const brand of brands) {
    const seoTitle = `${brand.name} Ricambi Originali: Esplosi e Manuali Tecnici | JollyGame`;
    const seoDescription = `Trova ricambi originali ${brand.name} per la tua piscina. Esplosi tecnici, manuali e pezzi di ricambio certificati per manutenzione e riparazione.`;
    
    const metaobject = {
      type: "brand_ricambi",
      handle: brand.handle,
      fields: [
        { key: "nome", value: brand.name },
        { key: "seo_title", value: seoTitle },
        { key: "seo_description", value: seoDescription },
        { key: "descrizione", value: JSON.stringify({
          type: "root",
          children: [
            {
              type: "paragraph",
              children: [
                { type: "text", value: `Benvenuti nella sezione dedicata ai ricambi originali ${brand.name}. Qui puoi trovare tutto il necessario per la manutenzione della tua piscina e dei tuoi accessori.` }
              ]
            }
          ]
        }) }
      ]
    };

    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query: mutation, variables: { metaobject } }),
    });

    const result = await response.json();
    console.log(`Brand ${brand.name} result:`, JSON.stringify(result, null, 2));
  }
}

run().catch(console.error);
