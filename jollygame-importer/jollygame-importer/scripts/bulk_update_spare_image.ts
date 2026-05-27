import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import mime from "mime-types";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function uploadFile(filePath: string) {
  const fileName = path.basename(filePath);
  const fileMime = mime.lookup(filePath) || "image/jpeg";
  const fileBuffer = fs.readFileSync(filePath);

  const stagedRes = await shopifyRequest(`
    mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
      stagedUploadsCreate(input: $input) {
        stagedTargets { url resourceUrl parameters { name value } }
      }
    }`, {
    input: [{ filename: fileName, mimeType: fileMime, resource: "IMAGE", fileSize: fileBuffer.length.toString(), httpMethod: "POST" }]
  });

  const target = stagedRes.data.stagedUploadsCreate.stagedTargets[0];
  const boundary = "----WebKitFormBoundary" + Math.random().toString(36).substring(2);
  let bodyParts: Buffer[] = [];
  for (const param of target.parameters) {
    bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${param.name}"\r\n\r\n${param.value}\r\n`));
  }
  bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${fileName}"\r\nContent-Type: ${fileMime}\r\n\r\n`));
  bodyParts.push(fileBuffer);
  bodyParts.push(Buffer.from(`\r\n--${boundary}--\r\n`));

  const body = Buffer.concat(bodyParts);

  await fetch(target.url, {
    method: "POST",
    headers: { "Content-Type": `multipart/form-data; boundary=${boundary}` },
    body: body
  });

  const createRes = await shopifyRequest(`
    mutation fileCreate($files: [FileCreateInput!]!) {
      fileCreate(files: $files) { files { id } }
    }`, {
    files: [{ alt: "R0516700 Vite", contentType: "IMAGE", originalSource: target.resourceUrl }]
  });

  return createRes.data.fileCreate.files[0].id;
}

async function run() {
  const sku = "R0516700";
  const filePath = path.resolve("../../downloads/ricambi_images/R0516700.jpg");

  console.log(`🚀 Uploading image for ${sku}...`);
  const fileId = await uploadFile(filePath);
  console.log(`✅ File created with ID: ${fileId}`);

  // Polling per sicurezza
  await new Promise(r => setTimeout(r, 5000));

  // 1. Trova tutti i Metaobject con questo SKU
  console.log(`🔎 Cerco tutti i Metaobject di tipo 'ricambio' con SKU ${sku}...`);
  const findRes = await shopifyRequest(`{
    metaobjects(type: "ricambio", first: 250, query: "sku_originale:${sku}") {
      nodes { id }
    }
  }`, {});

  const moIds = findRes.data.metaobjects.nodes.map(n => n.id);
  console.log(`📈 Trovati ${moIds.length} metaobject da aggiornare.`);

  // 2. Aggiorna tutti
  for (const id of moIds) {
      console.log(`  Updating ${id}...`);
      await shopifyRequest(`
        mutation metaobjectUpdate($id: ID!, $metaobject: MetaobjectUpdateInput!) {
          metaobjectUpdate(id: $id, metaobject: $metaobject) {
            userErrors { message }
          }
        }
      `, {
        id,
        metaobject: {
            fields: [{ key: "immagine", value: fileId }]
        }
      });
  }
  
  console.log("🎉 Aggiornamento completato!");
}

run().catch(console.error);
