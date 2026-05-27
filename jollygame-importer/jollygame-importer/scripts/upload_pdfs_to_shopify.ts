import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

const METAOBJECT_CREATE = `
mutation metaobjectCreate($metaobject: MetaobjectCreateInput!) {
  metaobjectCreate(metaobject: $metaobject) {
    metaobject { id }
    userErrors { field message }
  }
}
`;

const PRODUCT_UPDATE_METAFIELD = `
mutation productUpdate($input: ProductInput!) {
  productUpdate(input: $input) {
    product { id }
    userErrors { field message }
  }
}
`;

async function uploadAndLinkDocs() {
    console.log("🚀 Avvio caricamento e collegamento documentazione tecnica...");

    const docMap = JSON.parse(fs.readFileSync("extracted_documents_map.json", "utf-8"));

    // 1. Recupero prodotti esistenti
    const products: any[] = [];
    let hasNextPage = true;
    let cursor = null;
    while (hasNextPage) {
        const query = `
        query getProducts($cursor: String) {
          products(first: 250, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes { id handle title }
          }
        }
        `;
        const res = await shopifyRequest(query, { cursor });
        products.push(...res.data.products.nodes);
        hasNextPage = res.data.products.pageInfo.hasNextPage;
        cursor = res.data.products.pageInfo.endCursor;
    }
    console.log(`📦 Caricati ${products.length} prodotti da Shopify.`);

    // 2. Recupero Metaobjects esistenti (per evitare duplicati)
    const existingMetaobjects: Record<string, string> = {}; // url -> id
    let metaCursor = null;
    let metaHasNext = true;
    while (metaHasNext) {
        const metaQuery = `
        query getMeta($cursor: String) {
          metaobjects(first: 250, type: "documento_tecnico", after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              url_file: field(key: "url_file") { value }
            }
          }
        }
        `;
        const mRes = await shopifyRequest(metaQuery, { cursor: metaCursor });
        if (!mRes.data?.metaobjects) break;
        for (const m of mRes.data.metaobjects.nodes) {
            if (m.url_file) existingMetaobjects[m.url_file.value] = m.id;
        }
        metaHasNext = mRes.data.metaobjects.pageInfo.hasNextPage;
        metaCursor = mRes.data.metaobjects.pageInfo.endCursor;
    }
    console.log(`📚 Trovati ${Object.keys(existingMetaobjects).length} Metaobjects esistenti.`);

    let updatedCount = 0;

    for (const item of docMap) {
        const shopifyProduct = products.find(p => p.handle === item.handle || p.title.toLowerCase().trim() === item.productTitle.toLowerCase().trim());
        if (!shopifyProduct) continue;

        const metaIds: string[] = [];
        for (const doc of item.docs) {
            let metaId = existingMetaobjects[doc.url];
            if (!metaId) {
                // Crea Metaobject
                const createRes = await shopifyRequest(METAOBJECT_CREATE, {
                    metaobject: {
                        type: "documento_tecnico",
                        fields: [
                            { key: "titolo", value: doc.title },
                            { key: "url_file", value: doc.url }
                        ]
                    }
                });
                metaId = createRes.data?.metaobjectCreate?.metaobject?.id;
                if (metaId) {
                    existingMetaobjects[doc.url] = metaId;
                    console.log(`✨ Creato Metaobject per: ${doc.title}`);
                }
            }
            if (metaId) metaIds.push(metaId);
        }

        if (metaIds.length > 0) {
            // Aggiorna Metafield Prodotto
            const updateRes = await shopifyRequest(PRODUCT_UPDATE_METAFIELD, {
                input: {
                    id: shopifyProduct.id,
                    metafields: [
                        {
                            namespace: "custom",
                            key: "documentazione_tecnica",
                            value: JSON.stringify(metaIds),
                            type: "list.metaobject_reference"
                        }
                    ]
                }
            });
            if (updateRes.data?.productUpdate?.product) {
                updatedCount++;
                process.stdout.write(".");
            } else {
                console.error(`\n❌ Errore collegamento per ${shopifyProduct.title}:`, JSON.stringify(updateRes.data?.productUpdate?.userErrors));
            }
        }
    }

    console.log(`\n\n✅ Operazione completata! Collegati documenti a ${updatedCount} prodotti.`);
}

uploadAndLinkDocs().catch(console.error);
