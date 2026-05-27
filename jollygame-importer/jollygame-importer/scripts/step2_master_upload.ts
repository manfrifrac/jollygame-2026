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
      status
      image { url }
    }
  }
}
`;

async function uploadFile(filePath) {
  const fileName = path.basename(filePath);
  const fileMime = mime.lookup(filePath) || "image/jpeg";
  const fileBuffer = fs.readFileSync(filePath);

  const stagedRes = await shopifyRequest(STAGED_UPLOADS_CREATE, {
    input: [{ filename: fileName, mimeType: fileMime, resource: "IMAGE", fileSize: fileBuffer.length.toString(), httpMethod: "POST" }]
  });

  const target = stagedRes.data.stagedUploadsCreate.stagedTargets[0];
  const boundary = "----WebKitFormBoundary" + Math.random().toString(36).substring(2);
  let bodyParts = [];
  for (const param of target.parameters) {
    bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${param.name}"\r\n\r\n${param.value}\r\n`));
  }
  bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${fileName}"\r\nContent-Type: ${fileMime}\r\n\r\n`));
  bodyParts.push(fileBuffer);
  bodyParts.push(Buffer.from(`\r\n--${boundary}--\r\n`));

  const uploadRes = await fetch(target.url, {
    method: "POST",
    headers: { "Content-Type": `multipart/form-data; boundary=${boundary}` },
    body: Buffer.concat(bodyParts)
  });

  if (!uploadRes.ok) return null;

  const createRes = await shopifyRequest(FILE_CREATE, {
    files: [{ alt: "Esploso o Ricambio", contentType: "IMAGE", originalSource: target.resourceUrl }]
  });

  if (createRes.data?.fileCreate?.files?.length > 0) {
      return createRes.data.fileCreate.files[0].id;
  }
  return null;
}

async function run() {
  const downloadMap = JSON.parse(fs.readFileSync("download_map.json", "utf-8"));
  const uploadMap = {};
  
  if (fs.existsSync('upload_map.json')) {
      Object.assign(uploadMap, JSON.parse(fs.readFileSync('upload_map.json', 'utf-8')));
  }

  const urls = Object.keys(downloadMap);
  console.log(`Inizio upload di ${urls.length} immagini su Shopify...`);

  for (const url of urls) {
    if (uploadMap[url]) {
        console.log(`  ℹ️ Già caricato: ${url}`);
        continue;
    }

    const localPath = downloadMap[url];
    console.log(`🚀 Uploading: ${path.basename(localPath)}...`);
    
    try {
        const fileId = await uploadFile(localPath);
        if (fileId) {
            uploadMap[url] = fileId;
            console.log(`  ✅ ID: ${fileId}`);
            // Save progress periodically
            fs.writeFileSync('upload_map.json', JSON.stringify(uploadMap, null, 2));
        } else {
            console.error(`  ❌ Fallito upload per ${url}`);
        }
    } catch (err) {
        console.error(`  ❌ Errore per ${url}:`, err);
    }
    
    await new Promise(r => setTimeout(r, 1000));
  }
  
  console.log("\n🎉 Upload completato. Mappa salvata in upload_map.json");
}

run().catch(console.error);
