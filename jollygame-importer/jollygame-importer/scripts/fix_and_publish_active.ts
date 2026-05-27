import dotenv from "dotenv";

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

async function fixAndPublish() {
  console.log("🛠️ Inizio fase di pulizia titoli e pubblicazione canali...");

  // 1. Recuperiamo ID della pubblicazione "Online Store"
  const pubRes = await shopifyRequest(`{ publications(first: 10) { nodes { id name } } }`);
  const onlineStorePubId = pubRes.data?.publications?.nodes.find((n: any) => n.name.toLowerCase().includes("online store"))?.id;
  
  if (!onlineStorePubId) {
      console.error("❌ Impossibile trovare l'ID della pubblicazione Online Store");
      return;
  }
  console.log(`📍 Online Store Publication ID: ${onlineStorePubId}`);

  let hasNextPage = true;
  let cursor = null;

  while (hasNextPage) {
    const query = `
    query getActive($cursor: String) {
      products(first: 250, after: $cursor, query: "status:active") {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          descriptionHtml
          resourcePublicationsV2(first: 10) {
            nodes {
              publication { id name }
              isPublished
            }
          }
          variants(first: 1) { nodes { price } }
        }
      }
    }
    `;

    const res = await shopifyRequest(query, { cursor });
    if (!res.data?.products) break;

    for (const product of res.data.products.nodes) {
      let newTitle = product.title;
      let newDesc = product.descriptionHtml || "";
      let titleChanged = false;
      let descChanged = false;

      // Pulizia manuale basata sui pattern trovati
      if (newTitle.includes("\n\n(In alternativa")) {
          newTitle = newTitle.split("\n\n")[0];
          titleChanged = true;
      }
      if (newTitle.includes("SKU: [inserisciSKU]")) {
          newTitle = newTitle.replace(" \n\nSKU: [inserisciSKU]", "");
          titleChanged = true;
      }
      if (newTitle.toLowerCase().includes("rispondi solo con")) {
          newTitle = newTitle.replace(/rispondi solo con.*/gi, "");
          titleChanged = true;
      }

      // Pulizia descrizione
      const aiPatterns = [
        /Ecco una descrizione ottimizzata:?/gi,
        /Nuovo titolo:.*$/gim,
        /Rispondi solo con.*$/gim,
        /Sei un esperto di copywriting.*$/gim,
        /SKU: \[inserisciSKU\]/gi
      ];

      for (const pattern of aiPatterns) {
          if (pattern.test(newDesc)) {
              newDesc = newDesc.replace(pattern, "");
              descChanged = true;
          }
      }

      const isPublished = product.resourcePublicationsV2.nodes.some((p: any) => p.publication.id === onlineStorePubId && p.isPublished);
      const price = parseFloat(product.variants.nodes[0]?.price || "0");

      if (titleChanged || descChanged) {
          console.log(`✨ Pulizia Dati: "${product.title}"`);
          const updateInput: any = { id: product.id };
          if (titleChanged) updateInput.title = newTitle.trim();
          if (descChanged) updateInput.descriptionHtml = newDesc.trim();
          
          await shopifyRequest(`mutation productUpdate($input: ProductInput!) { productUpdate(input: $input) { product { id } } }`, { input: updateInput });
      }

      // Se è attivo e ha prezzo > 0, ma non è pubblicato online, lo pubblichiamo
      if (price > 0 && !isPublished) {
          console.log(`🚀 Pubblicazione Online: ${newTitle}`);
          const publishMutation = `
          mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
            publishablePublish(id: $id, input: $input) {
              userErrors { message }
            }
          }
          `;
          await shopifyRequest(publishMutation, {
              id: product.id,
              input: [{ publicationId: onlineStorePubId }]
          });
      }
    }

    hasNextPage = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log("\n✅ Operazione di pulizia e pubblicazione completata!");
}

fixAndPublish().catch(console.error);
