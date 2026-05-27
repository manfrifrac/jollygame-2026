import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import mime from "mime-types";

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

const STAGED_UPLOADS_CREATE = `
mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
  stagedUploadsCreate(input: $input) {
    stagedTargets {
      url
      resourceUrl
      parameters { name value }
    }
  }
}
`;

const FILE_CREATE = `
mutation fileCreate($files: [FileCreateInput!]!) {
  fileCreate(files: $files) {
    files { id fileStatus }
  }
}
`;

const GET_FILE = `
query getFile($id: ID!) {
  node(id: $id) {
    ... on MediaImage {
      image { url }
    }
  }
}
`;

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
    product { id }
    userErrors { field message }
  }
}
`;

async function uploadFile(filePath) {
  const fileName = path.basename(filePath);
  const fileMime = mime.lookup(filePath) || "image/jpeg";
  const fileBuffer = fs.readFileSync(filePath);

  console.log(`  - Creazione staged upload per ${fileName}...`);
  const stagedRes = await shopifyRequest(STAGED_UPLOADS_CREATE, {
    input: [{ filename: fileName, mimeType: fileMime, resource: "IMAGE", fileSize: fileBuffer.length.toString(), httpMethod: "POST" }]
  });

  if (!stagedRes.data?.stagedUploadsCreate?.stagedTargets) {
      console.error("  ❌ Errore Staged Upload:", JSON.stringify(stagedRes, null, 2));
      return null;
  }

  const target = stagedRes.data.stagedUploadsCreate.stagedTargets[0];
  const boundary = "----WebKitFormBoundary" + Math.random().toString(36).substring(2);
  let bodyParts = [];
  for (const param of target.parameters) {
    bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${param.name}"\r\n\r\n${param.value}\r\n`));
  }
  bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${fileName}"\r\nContent-Type: ${fileMime}\r\n\r\n`));
  bodyParts.push(fileBuffer);
  bodyParts.push(Buffer.from(`\r\n--${boundary}--\r\n`));

  console.log(`  - Invio file binario a Google Storage...`);
  const uploadRes = await fetch(target.url, {
    method: "POST",
    headers: { "Content-Type": `multipart/form-data; boundary=${boundary}` },
    body: Buffer.concat(bodyParts)
  });

  if (!uploadRes.ok) {
      console.error(`  ❌ Invio fallito: ${uploadRes.status}`, await uploadRes.text());
      return null;
  }

  console.log(`  - Creazione record File su Shopify...`);
  const createRes = await shopifyRequest(FILE_CREATE, {
    files: [{ alt: "Esploso Tecnico", contentType: "IMAGE", originalSource: target.resourceUrl }]
  });

  if (createRes.errors || createRes.data?.fileCreate?.userErrors?.length > 0) {
      console.error("  ❌ Errore File Create:", JSON.stringify(createRes, null, 2));
      return null;
  }

  const fileId = createRes.data.fileCreate.files[0].id;
  console.log(`  - File creato con ID: ${fileId}. Polling per URL pubblico...`);
  
  // Wait for file status ready
  let url = null;
  for (let i = 0; i < 8; i++) {
    await new Promise(r => setTimeout(r, 4000));
    const fileRes = await shopifyRequest(GET_FILE, { id: fileId });
    url = fileRes.data?.node?.image?.url;
    if (url) {
        console.log(`  - URL ottenuto al tentativo ${i+1}`);
        break;
    }
    console.log(`    ...attesa (tentativo ${i+1}/8)`);
  }
  return url;
}

async function run() {
  const matches = JSON.parse(fs.readFileSync("esplosi_matches.json", "utf-8"));
  console.log(`Caricamento di ${matches.length} esplosi su Shopify...`);

  for (const match of matches) {
    if (!match.local_file) continue;
    console.log(`Processing ${match.title}...`);
    
    try {
        const publicUrl = await uploadFile(match.local_file);
        if (!publicUrl) {
            console.error(`  ❌ Failed to get public URL for ${match.title}`);
            continue;
        }

        // Create metaobject
        const moRes = await shopifyRequest(METAOBJECT_CREATE, {
            metaobject: {
                type: "documento_tecnico",
                fields: [
                    { key: "titolo", value: "Esploso Tecnico " + match.sku },
                    { key: "url_file", value: publicUrl }
                ]
            }
        });

        const moId = moRes.data.metaobjectCreate.metaobject?.id;
        if (!moId) {
            console.error(`  ❌ Failed to create metaobject for ${match.title}`, moRes.data.metaobjectCreate.userErrors);
            continue;
        }

        // Update product
        const currentDocs = JSON.parse(match.current_docs || "[]");
        if (!currentDocs.includes(moId)) {
            currentDocs.push(moId);
            await shopifyRequest(PRODUCT_UPDATE, {
                input: {
                    id: match.shopify_id,
                    metafields: [{
                        namespace: "custom",
                        key: "documentazione_tecnica",
                        value: JSON.stringify(currentDocs)
                    }]
                }
            });
            console.log(`  ✅ Linked Esploso to ${match.title}`);
        } else {
            console.log(`  ℹ️ Already linked to ${match.title}`);
        }
    } catch (err) {
        console.error(`  ❌ Error processing ${match.title}:`, err);
    }
    
    // Pause to avoid rate limits
    await new Promise(r => setTimeout(r, 1000));
  }
}

run().catch(console.error);
