import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";
const GRAPHQL_URL = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`;

async function shopifyRequest(query: string, variables: any = {}) {
  const response = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query, variables }),
  });
  return await response.json();
}

async function auditMainMenu() {
  console.log("🔍 Analisi Main Menu e Collegamenti Handle...");

  // Nota: I menu (LinkLists) non sono ancora pienamente supportati in modo semplice via Admin GraphQL 
  // per recuperare i singoli link in profondità, ma possiamo provare a recuperare le LinkLists
  // e vedere se il tema usa metafields o una navigazione standard.
  
  // In alternativa, usiamo l'API REST per i menu che è più affidabile per questo compito specifico
  const restUrl = `https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/link_lists.json`;
  
  const response = await fetch(restUrl, {
    method: "GET",
    headers: {
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    }
  });
  
  const data = await response.json();
  const mainMenus = data.link_lists;

  if (!mainMenus) {
    console.log("Nessun menu trovato via REST.");
    return;
  }

  console.log("\n🗺️ MAPPATURA MENU:");
  mainMenus.forEach((menu: any) => {
    console.log(`\n📂 Menu: ${menu.title} (Handle: ${menu.handle})`);
    menu.links.forEach((link: any) => {
      console.log(`  - ${link.title} -> ${link.type} : ${link.subject_params?.handle || link.url}`);
      // Se ci sono sottolivelli
      // Nota: REST non restituisce ricorsivamente tutti i livelli in un solo colpo se sono annidati via "links"
      // ma in questo store solitamente il main-menu ha i link diretti o i primi livelli.
    });
  });

  console.log("\n✅ Analisi menu completata.");
}

auditMainMenu().catch(console.error);
