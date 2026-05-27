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

async function inspectMetaobject() {
  const query = `
  {
    products(first: 5, query: "vendor:'Zodiac'") {
      nodes {
        title
        metafields(first: 10, namespace: "custom") {
          nodes {
            key
            value
            reference {
              ... on Metaobject {
                type
                fields {
                  key
                  value
                  reference {
                    ... on GenericFile {
                      url
                    }
                    ... on MediaImage {
                      image { url }
                    }
                  }
                }
              }
            }
            references(first: 10) {
              nodes {
                ... on Metaobject {
                  type
                  fields {
                    key
                    value
                    reference {
                      ... on GenericFile {
                        url
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  `;

  const res = await shopifyRequest(query);
  const products = res.data?.products?.nodes || [];
  
  console.log("--- Ispezione Documentazione Tecnica Metaobject ---");
  products.forEach((p: any) => {
    console.log(`\n📦 ${p.title}`);
    p.metafields.nodes.forEach((m: any) => {
      if (m.key === 'documentazione_tecnica') {
          console.log(`   - custom.documentazione_tecnica:`);
          if (m.references && m.references.nodes.length > 0) {
              m.references.nodes.forEach((mo: any) => {
                  console.log(`     Metaobject Type: ${mo.type}`);
                  mo.fields.forEach((f: any) => {
                      console.log(`       -> Field '${f.key}': ${f.value} (Reference URL: ${f.reference?.url || 'N/A'})`);
                  });
              });
          } else if (m.reference) {
              console.log(`     Single Metaobject Type: ${m.reference.type}`);
          } else {
              console.log(`     Raw value: ${m.value}`);
          }
      }
    });
  });
}

inspectMetaobject().catch(console.error);
