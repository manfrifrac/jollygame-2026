import fs from "fs";
import dotenv from "dotenv";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query, variables) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN },
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

const PRODUCT_UPDATE = `
mutation productUpdate($input: ProductInput!) {
  productUpdate(input: $input) {
    userErrors { field message }
  }
}
`;

async function run() {
  const masterData = JSON.parse(fs.readFileSync("master_sync_data.json", "utf-8"));
  const uploadMap = JSON.parse(fs.readFileSync("upload_map.json", "utf-8"));

  console.log(`🚀 Sincronizzazione di ${masterData.length} prodotti...`);

  for (const product of masterData) {
    console.log(`📦 Elaborazione: ${product.shopify_title}...`);
    
    try {
        // 1. Create unique Metaobjects for each spare part
        const moIds = [];
        for (const r of product.ricambi) {
            const fullTitle = `${r.title} [${product.shopify_title} Rif.${r.index}]`;
            
            // Get image ID if exists
            let imageId = null;
            if (r.images && r.images !== '[]' && r.images !== '') {
                try {
                    let firstUrl = null;
                    if (product.db === 'Fluidra') {
                        const imgs = JSON.parse(r.images);
                        if (imgs.length > 0) firstUrl = imgs[0];
                    } else {
                        firstUrl = r.images.split(',')[0].strip();
                    }
                    firstUrl = r.images.split(',')[0].trim();
                    } catch(e) {}
                    }

                    const fields = [
                    { key: "nome", value: r.title },
                    { key: "sku_originale", value: r.sku },
                    { key: "riferimento_esploso", value: String(r.index) }
                    ];
                    if (imageId) fields.push({ key: "immagine", value: imageId });

                    const moRes = await shopifyRequest(METAOBJECT_CREATE, {
                    metaobject: {
                    type: "ricambio",
                    fields: fields,
                    capabilities: { publishable: { status: "ACTIVE" } }
                    }
                    });

                    const moId = moRes.data?.metaobjectCreate?.metaobject?.id;
                    if (moId) moIds.push(moId);
                    }

        // 2. Prepare Metafields
        const metafields = [];
        
        // Diagram Image
        if (product.diagram_url && uploadMap[product.diagram_url]) {
            metafields.push({
                namespace: "custom",
                key: "immagine_esploso",
                value: uploadMap[product.diagram_url]
            });
        }

        // Spare Parts List
        if (moIds.length > 0) {
            metafields.push({
                namespace: "custom",
                key: "lista_ricambi_esploso",
                value: JSON.stringify(moIds)
            });
        }

        // 3. Update Product
        if (metafields.length > 0) {
            await shopifyRequest(PRODUCT_UPDATE, {
                input: {
                    id: product.shopify_id,
                    metafields: metafields
                }
            });
            console.log(`  ✅ Collegati ${moIds.length} ricambi e l'esploso.`);
        }

    } catch (err) {
        console.error(`  ❌ Errore per ${product.shopify_title}:`, err);
    }
    
    // Rate limit protection
    await new Promise(r => setTimeout(r, 1000));
  }
}

run().catch(console.error);
