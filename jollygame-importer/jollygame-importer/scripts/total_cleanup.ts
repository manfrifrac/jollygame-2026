import fs from "fs";
import path from "path";
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

async function totalCleanup() {
  console.log("🌟 Avvio Bonifica Finale (SKU + Immagini + Canali)...");

  // 1. Carico i nuovi SKU trovati
  const skuPath = path.resolve("../../sku_audit_results.json");
  const auditData = fs.existsSync(skuPath) ? JSON.parse(fs.readFileSync(skuPath, "utf-8")) : [];

  // 2. Recupero canali di vendita
  const pubQuery = `{ publications(first: 50) { nodes { id name } } }`;
  const pubRes = await shopifyRequest(pubQuery);
  const publications = pubRes.data?.publications?.nodes || [];
  const googleChannel = publications.find((p: any) => p.name.toLowerCase().includes("google"));
  const youtubeChannel = publications.find((p: any) => p.name.toLowerCase().includes("youtube"));

  // 3. Recupero tutti i prodotti con media
  const productsQuery = `
  {
    products(first: 250) {
      nodes {
        id
        title
        media(first: 20) { nodes { id mediaContentType ... on MediaImage { image { url } } } }
        variants(first: 1) { nodes { id sku price } }
      }
    }
  }
  `;
  const prodRes = await shopifyRequest(productsQuery);
  const products = prodRes.data.products.nodes;

  for (const product of products) {
    console.log(`\n📦 Elaborazione: ${product.title}`);

    // A. Aggiornamento SKU
    const auditMatch = auditData.find((a: any) => a.title.toLowerCase().trim() === product.title.toLowerCase().trim());
    if (auditMatch && auditMatch.new_sku && !product.variants.nodes[0]?.sku) {
        console.log(`  📎 Impostazione SKU: ${auditMatch.new_sku}`);
        await shopifyRequest(`
          mutation productVariantUpdate($input: ProductVariantInput!) {
            productVariantUpdate(input: $input) { productVariant { id sku } }
          }
        `, { input: { id: product.variants.nodes[0].id, sku: auditMatch.new_sku } });
    }

    // B. Deduplicazione Immagini (Deep)
    const images = product.media.nodes.filter((m: any) => m.mediaContentType === 'IMAGE');
    const seenFiles = new Set();
    const toDelete = [];
    for (const img of images) {
        const file = img.image?.url?.split('/').pop()?.split('?')[0];
        if (seenFiles.has(file)) {
            toDelete.push(img.id);
        } else {
            seenFiles.add(file);
        }
    }
    if (toDelete.length > 0) {
        console.log(`  👯 Eliminazione ${toDelete.length} immagini doppie.`);
        await shopifyRequest(`
          mutation productDeleteMedia($mediaIds: [ID!]!, $productId: ID!) {
            productDeleteMedia(mediaIds: $mediaIds, productId: $productId) { deletedMediaIds }
          }
        `, { productId: product.id, mediaIds: toDelete });
    }

    // C. Canali di Vendita
    const price = parseFloat(product.variants.nodes[0]?.price || "0");
    if (price === 0) {
        console.log(`  🚫 Prezzo 0: Rimozione da Google/YouTube.`);
        const unpubInput = [];
        if (googleChannel) unpubInput.push({ publicationId: googleChannel.id });
        if (youtubeChannel) unpubInput.push({ publicationId: youtubeChannel.id });
        await shopifyRequest(`
          mutation publishableUnpublish($id: ID!, $input: [PublicationInput!]!) {
            publishableUnpublish(id: $id, input: $input) { userErrors { message } }
          }
        `, { id: product.id, input: unpubInput });
    }
  }

  console.log("\n✨ Bonifica finale completata con successo.");
}

totalCleanup().catch(console.error);
