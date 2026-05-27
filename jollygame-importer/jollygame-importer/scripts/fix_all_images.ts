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
  }
}
`;

const PRODUCT_CREATE_MEDIA = `
mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
  productCreateMedia(media: $media, productId: $productId) {
    media { id }
    userErrors { message }
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
  const fileBuffer = fs.readFileSync(filePath);

  const stagedRes = await shopifyRequest(STAGED_UPLOADS_CREATE, {
    input: [{ filename: fileName, mimeType: fileMime, resource: "PRODUCT_IMAGE", fileSize: fileBuffer.length.toString(), httpMethod: "POST" }]
  });

  const target = stagedRes.data?.stagedUploadsCreate?.stagedTargets[0];
  if (!target) return null;

  const boundary = "----WebKitFormBoundary" + Math.random().toString(36).substring(2);
  let bodyParts: Buffer[] = [];

  // Add parameters
  for (const param of target.parameters) {
    bodyParts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${param.name}"\r\n\r\n${param.value}\r\n`));
  }

  // Add file
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
    console.error(`  ❌ Failed: ${res.status}`, await res.text());
    return null;
  }

  return target.resourceUrl;
}

function normalize(s: string) {
    return s.toLowerCase().replace(/[^a-z0-9]/g, '');
}

async function fixAllImages() {
  console.log("🔍 Avvio riparazione immagini (Metodo Manuale - Pagina Completa)...");

  let hasNextPage = true;
  let cursor = null;
  const allProducts: any[] = [];

  while (hasNextPage) {
    const productsQuery = `
      query getProducts($cursor: String) {
        products(first: 250, after: $cursor, reverse: true) {
          pageInfo { hasNextPage endCursor }
          nodes { id title handle }
        }
      }
    `;
    const prodRes = await shopifyRequest(productsQuery, { cursor });
    if (!prodRes.data?.products) break;

    allProducts.push(...prodRes.data.products.nodes);
    hasNextPage = prodRes.data.products.pageInfo.hasNextPage;
    cursor = prodRes.data.products.pageInfo.endCursor;
    console.log(`Recuperati ${allProducts.length} prodotti...`);
  }

  const imageDirs = [path.resolve("../../zodiac_images"), path.resolve("../../laghetto_images")];
  const folderMap: Record<string, string> = {};
  for (const base of imageDirs) {
      if (fs.existsSync(base)) {
          fs.readdirSync(base).forEach(folder => {
              folderMap[normalize(folder)] = path.join(base, folder);
          });
      }
  }

  for (const product of allProducts) {
    let localPath = folderMap[normalize(product.title)] || folderMap[normalize(product.handle)];

    if (localPath) {
      console.log(`\n📸 Prodotto: ${product.title}`);
      const files = fs.readdirSync(localPath).filter(f => /\.(jpg|jpeg|png|webp)$/i.test(f)).slice(0, 5);
      const media = [];
      for (const file of files) {
        process.stdout.write(`  ⬆️ Caricamento ${file}... `);
        const url = await uploadFile(path.join(localPath, file));
        if (url) {
            console.log("OK");
            media.push({ alt: product.title, mediaContentType: "IMAGE", originalSource: url as string });
        }
      }
      
      if (media.length > 0) {
        const res = await shopifyRequest(PRODUCT_CREATE_MEDIA, { productId: product.id, media });
        console.log(res.data?.productCreateMedia?.userErrors?.length ? "❌ Errore Link" : "✅ Immagini collegate");
      }
    }
  }
}

fixAllImages().catch(console.error);
