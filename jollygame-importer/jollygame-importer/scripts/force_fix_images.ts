import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import mime from "mime-types";
import FormData from "form-data";

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
  }
}
`;

const PRODUCT_CREATE_MEDIA = `
mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
  productCreateMedia(media: $media, productId: $productId) {
    media { id status }
    userErrors { field message }
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

async function uploadFile(filePath: string) {
  const fileName = path.basename(filePath);
  const fileMime = mime.lookup(filePath) || "image/jpeg";
  const fileSize = fs.statSync(filePath).size;

  const stagedRes = await shopifyRequest(STAGED_UPLOADS_CREATE, {
    input: [{ 
      filename: fileName, 
      mimeType: fileMime, 
      resource: "PRODUCT_IMAGE", 
      fileSize: fileSize.toString(),
      httpMethod: "POST"
    }]
  });

  const target = stagedRes.data?.stagedUploadsCreate?.stagedTargets[0];
  if (!target) return null;

  // Manually build the form to ensure NO extra headers like 'Known-Length' or content-type per part
  const form = new FormData();
  
  // Rule: Add all parameters EXACTLY as they are
  target.parameters.forEach((p: any) => {
      form.append(p.name, p.value);
  });
  
  // Rule: Add the file LAST, as a stream, without extra options that could bloat the part header
  form.append("file", fs.createReadStream(filePath));

  return new Promise((resolve) => {
      // form.submit handles the boundary correctly and avoids 'transfer-encoding: chunked' which S3/GCS often hate
      form.submit(target.url, (err, res) => {
          if (err) {
              console.error(`  ❌ Submit error:`, err);
              return resolve(null);
          }
          
          let body = '';
          res.on('data', chunk => body += chunk);
          res.on('end', () => {
              if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                  resolve(target.resourceUrl);
              } else {
                  // If signature still fails, we'll see the exact canonical request Shopify signed vs what was sent
                  console.error(`  ❌ Upload failed (${res.statusCode}):`, body);
                  resolve(null);
              }
          });
      });
  });
}

function normalize(s: string) {
    return s.toLowerCase().replace(/[^\w]/g, '');
}

async function forceFixImages() {
  console.log("🔍 Fetching products...");
  const productsQuery = `{ products(first: 50, reverse: true) { nodes { id title handle } } }`;
  const prodRes = await shopifyRequest(productsQuery, {});
  const products = prodRes.data.products.nodes;

  const imageDirs = [path.resolve("../../zodiac_images"), path.resolve("../../laghetto_images")];
  const folderMap: Record<string, string> = {};
  for (const base of imageDirs) {
      if (fs.existsSync(base)) {
          fs.readdirSync(base).forEach(folder => {
              folderMap[normalize(folder)] = path.join(base, folder);
          });
      }
  }

  for (const product of products) {
    let localPath = folderMap[normalize(product.title)] || folderMap[normalize(product.handle)];

    if (localPath) {
      console.log(`\n📸 Folder: ${product.title}`);
      const files = fs.readdirSync(localPath).filter(f => /\.(jpg|jpeg|png|webp)$/i.test(f)).slice(0, 3);
      const media = [];
      for (const file of files) {
        process.stdout.write(`  ⬆️ ${file}... `);
        const url = await uploadFile(path.join(localPath, file));
        if (url) {
            console.log("OK");
            media.push({ alt: product.title, mediaContentType: "IMAGE", originalSource: url as string });
        }
      }
      
      if (media.length > 0) {
        const res = await shopifyRequest(PRODUCT_CREATE_MEDIA, { productId: product.id, media });
        if (res.data?.productCreateMedia?.userErrors.length > 0) {
            console.log("❌ Link Error:", res.data.productCreateMedia.userErrors[0].message);
        } else {
            console.log("✅ Success");
        }
      }
    }
  }
}

forceFixImages().catch(console.error);
