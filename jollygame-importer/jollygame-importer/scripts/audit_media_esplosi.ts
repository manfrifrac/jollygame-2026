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

async function auditMediaAndEsplosi() {
  console.log("🔍 Avvio Audit Media ed Esplosi Tecnici...");

  let hasNextPage = true;
  let cursor = null;
  const auditReport: any[] = [];

  while (hasNextPage) {
    const query = `
    query getMediaAudit($cursor: String) {
      products(first: 250, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          vendor
          mediaCount { count }
          media(first: 20) {
            nodes {
              mediaContentType
              status
              ... on Video {
                sources { url }
              }
              ... on MediaImage {
                image { url }
              }
              ... on Model3d {
                sources { url }
              }
            }
          }
          documentazione: metafield(namespace: "custom", key: "documentazione_tecnica") {
            value
          }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      const imagesCount = product.media.nodes.filter((m: any) => m.mediaContentType === "IMAGE").length;
      const videosCount = product.media.nodes.filter((m: any) => m.mediaContentType === "VIDEO").length;
      
      // Gli "esplosi" sono solitamente linkati nel metafield custom.documentazione_tecnica 
      // o sono PDF/Immagini specifiche. Verifichiamo se il metafield ha valore.
      const hasEsplosi = product.documentazione ? true : false;
      const esplosiContent = product.documentazione ? product.documentazione.value : null;

      auditReport.push({
        title: product.title,
        vendor: product.vendor,
        images_count: imagesCount,
        videos_count: videosCount,
        has_technical_docs: hasEsplosi,
        docs_reference: esplosiContent
      });
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
    console.log(`Analizzati ${auditReport.length} prodotti...`);
  }

  const stats = {
    total: auditReport.length,
    with_images: auditReport.filter(p => p.images_count > 0).length,
    without_images: auditReport.filter(p => p.images_count === 0).length,
    with_docs: auditReport.filter(p => p.has_technical_docs).length,
    without_docs: auditReport.filter(p => !p.has_technical_docs).length,
    with_videos: auditReport.filter(p => p.videos_count > 0).length
  };

  console.log("\n📊 RIEPILOGO MEDIA ED ESPLOSI:");
  console.table(stats);

  fs.writeFileSync("media_esplosi_audit.json", JSON.stringify({ stats, details: auditReport }, null, 2));
  console.log("\n✅ Audit completato. Report salvato in 'media_esplosi_audit.json'");
  
  // Esempio di prodotti senza documenti
  const missingDocs = auditReport.filter(p => !p.has_technical_docs).slice(0, 10);
  if (missingDocs.length > 0) {
      console.log("\n⚠️ Esempi di prodotti SENZA documentazione tecnica/esplosi:");
      missingDocs.forEach(p => console.log(`- ${p.title} (${p.vendor})`));
  }
}

auditMediaAndEsplosi().catch(console.error);
