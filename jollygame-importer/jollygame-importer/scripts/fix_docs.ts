import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function createMetaobject(titolo: string, url: string) {
  const mutation = `
  mutation metaobjectCreate($input: MetaobjectCreateInput!) {
    metaobjectCreate(metaobject: $input) {
      metaobject { id }
      userErrors { message }
    }
  }
  `;
  const input = {
    type: "documento_tecnico",
    fields: [
      { key: "titolo", value: titolo },
      { key: "url_file", value: url }
    ]
  };
  const res = await shopifyRequest(mutation, { input });
  return res.data?.metaobjectCreate?.metaobject?.id;
}

async function fixDocs() {
  console.log("🛠️ Inizio bonifica Metaobject PDF...");
  
  const query = `{
    products(first: 100, query: "metafield:custom.documentazione_tecnica IS NOT NULL") {
      nodes {
        id
        title
        metafields(first: 5, namespace: "custom") {
            nodes {
                id
                key
                references(first: 5) {
                    nodes {
                        id
                        fields { key value }
                    }
                }
            }
        }
      }
    }
  }`;
  
  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];

  for (const p of products) {
    const docsMetafield = p.metafields.nodes.find((m: any) => m.key === 'documentazione_tecnica');
    if (!docsMetafield) continue;

    const newMetaobjectIds = [];
    
    for (const mo of docsMetafield.references.nodes) {
        const urlField = mo.fields.find((f: any) => f.key === 'url_file');
        const titleField = mo.fields.find((f: any) => f.key === 'titolo');
        
        if (urlField && urlField.value.includes(';')) {
            const urls = urlField.value.split(';').map((u: string) => u.trim());
            const titles = titleField ? titleField.value.split(';').map((t: string) => t.trim()) : [];
            
            for (let i = 0; i < urls.length; i++) {
                const cleanUrl = urls[i];
                const cleanTitle = titles[i] || `Documento ${i+1}`;
                console.log(`  ➕ Creazione nuovo metaobject per: ${cleanTitle}`);
                const newId = await createMetaobject(cleanTitle, cleanUrl);
                if (newId) newMetaobjectIds.push(newId);
            }
        } else {
            newMetaobjectIds.push(mo.id);
        }
    }

    if (newMetaobjectIds.length > 0) {
        console.log(`  🔗 Aggiornamento prodotto: ${p.title}`);
        await shopifyRequest(`mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) { userErrors { message } }
        }`, { input: { id: p.id, metafields: [{ id: docsMetafield.id, values: JSON.stringify(newMetaobjectIds) }] } });
    }
  }
  console.log("✅ Bonifica completata.");
}

fixDocs().catch(console.error);
