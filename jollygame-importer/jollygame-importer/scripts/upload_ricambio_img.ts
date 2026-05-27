import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import mime from "mime-types";

dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

const STAGED_UPLOADS_CREATE = `
mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
  stagedUploadsCreate(input: $input) {
    stagedTargets {
      url
      resourceUrl
      parameters { name value }
    }
    userErrors { field message }
  }
}
`;

const FILE_CREATE = `
mutation fileCreate($files: [FileCreateInput!]!) {
  fileCreate(files: $files) {
    files {
      id
      fileStatus
    }
    userErrors {
      field
      message
    }
  }
}
`;

const METAOBJECT_UPDATE = `
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

async function shopifyRequest(query: string, variables: any) {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": ACCESS_TOKEN! },
    body: JSON.stringify({ query, variables }),
  });
  return await res.json();
}

async function uploadAndLink() {
  const filePath = path.resolve("../../downloads/ricambi_images/R0516700.jpeg");
  console.log("Uploading:", filePath);
  
  if (!fs.existsSync(filePath)) {
      console.error("File not found!");
      return;
  }

  const fileName = path.basename(filePath);
  const fileMime = mime.lookup(filePath) || "image/jpeg";
  const fileBuffer = fs.readFileSync(filePath);

  const stagedRes = await shopifyRequest(STAGED_UPLOADS_CREATE, {
    input: [{ filename: fileName, mimeType: fileMime, resource: "IMAGE", fileSize: fileBuffer.length.toString(), httpMethod: "POST" }]
  });

  const target = stagedRes.data?.stagedUploadsCreate?.stagedTargets[0];
  if (!target) {
      console.error("No staged target", stagedRes);
      return;
  }

  const boundary = "----WebKitFormBoundary" + Math.random().toString(36).substring(2);
  let bodyParts: Buffer[] = [];

  for (const param of target.parameters) {
    bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${param.name}"\r\n\r\n${param.value}\r\n`));
  }

  bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${fileName}"\r\nContent-Type: ${fileMime}\r\n\r\n`));
  bodyParts.push(fileBuffer);
  bodyParts.push(Buffer.from(`\r\n--${boundary}--\r\n`));

  const body = Buffer.concat(bodyParts);

  const res = await fetch(target.url, {
    method: "POST",
    headers: { "Content-Type": `multipart/form-data; boundary=${boundary}` },
    body: body
  });

  if (!res.ok) {
    console.error(`Upload Failed: ${res.status}`, await res.text());
    return;
  }

  console.log("File uploaded to staging. Creating File in Shopify...");

  const createRes = await shopifyRequest(FILE_CREATE, {
      files: [{
          alt: "R0516700 Vite",
          contentType: "IMAGE",
          originalSource: target.resourceUrl
      }]
  });

  if (!createRes.data || !createRes.data.fileCreate) {
      console.error("File creation response error:", JSON.stringify(createRes, null, 2));
      return;
  }

  if (createRes.data.fileCreate.userErrors?.length > 0) {
      console.error("File creation user errors:", createRes.data.fileCreate.userErrors);
      return;
  }

  const fileId = createRes.data.fileCreate.files[0].id;
  console.log("File created with ID:", fileId);

  // Wait a few seconds for the file to be ready
  await new Promise(r => setTimeout(r, 5000));

  console.log("Updating Metaobject...");
  const updateRes = await shopifyRequest(METAOBJECT_UPDATE, {
      id: "gid://shopify/Metaobject/532151697756",
      metaobject: {
          fields: [
              {
                  key: "immagine",
                  value: fileId
              }
          ]
      }
  });

  console.log("Metaobject Update Result:", JSON.stringify(updateRes, null, 2));
}

uploadAndLink().catch(console.error);
