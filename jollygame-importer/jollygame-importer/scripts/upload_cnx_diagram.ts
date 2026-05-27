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

  await fetch(target.url, {
    method: "POST",
    headers: { "Content-Type": `multipart/form-data; boundary=${boundary}` },
    body: Buffer.concat(bodyParts)
  });

  const createRes = await shopifyRequest(`
    mutation fileCreate($files: [FileCreateInput!]!) {
      fileCreate(files: $files) { files { id } }
    }`, {
    files: [{ alt: "Esploso Tecnico", contentType: "IMAGE", originalSource: target.resourceUrl }]
  });

  return createRes.data.fileCreate.files[0].id;
}

async function run() {
  const cnxSku = "WR000500"; // CNX 50 iQ
  const cnxId = "gid://shopify/Product/15546245513564";
  const filePath = path.resolve("../../downloads/esplosi/WR000500_esploso.jpeg");

  console.log("🚀 Caricamento Esploso per CNX 50 iQ...");
  const fileId = await uploadFile(filePath);
  console.log("✅ File caricato con ID:", fileId);

  // Aspettiamo che Shopify processi il file
  await new Promise(r => setTimeout(r, 5000));

  const updateRes = await shopifyRequest(`
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        userErrors { field message }
      }
    }
  `, {
    input: {
        id: cnxId,
        metafields: [{
            namespace: "custom",
            key: "immagine_esploso",
            value: fileId
        }]
    }
  });

  console.log("✅ Prodotto aggiornato:", JSON.stringify(updateRes, null, 2));
}

run().catch(console.error);
