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

const ENGLISH_KEYWORDS = [
    " the ", " and ", " performance ", " patented ", " suction ", " powerful ", " cleaning ",
    " integrated ", " coverage ", " agility ", " ideal ", " surfaces ", " filtration ",
    " collect ", " debris ", " efficiently ", " smallest ", " perfectly ", " clean ", " year round ",
    " smart sensors ", " unique design ", " embedded ", " limitless ", " shapes "
];

function detectLanguage(text: string): "it" | "en" | "mixed" {
    if (!text) return "it";
    const lowerText = text.toLowerCase();
    
    let enCount = 0;
    for (const word of ENGLISH_KEYWORDS) {
        if (lowerText.includes(word)) enCount++;
    }

    const hasItalian = / (di|il|lo|la|i|gli|le|un|uno|una|per|con|su|per|tra|fra) /.test(lowerText);
    const hasEnglish = enCount > 2;

    if (hasItalian && hasEnglish) return "mixed";
    if (hasEnglish) return "en";
    return "it";
}

async function auditProducts() {
  console.log("🔍 Avvio Audit Linguistico dei prodotti online...");

  const query = `
  query($cursor: String) {
    products(first: 250, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        vendor
        descriptionHtml
      }
    }
  }
  `;

  let hasNext = true;
  let cursor = null;
  const results = {
      it: [] as any[],
      en: [] as any[],
      mixed: [] as any[]
  };

  while (hasNext) {
    const res = await shopifyRequest(query, { cursor });
    if (!res.data) {
        console.error("Errore API:", JSON.stringify(res, null, 2));
        break;
    }
    const nodes = res.data.products.nodes;
    
    for (const product of nodes) {
        const fullText = `${product.title} ${product.descriptionHtml.replace(/<[^>]*>/g, ' ')}`;
        const lang = detectLanguage(fullText);
        results[lang].push({
            id: product.id,
            title: product.title,
            vendor: product.vendor
        });
    }

    hasNext = res.data.products.pageInfo.hasNextPage;
    cursor = res.data.products.pageInfo.endCursor;
  }

  console.log("\n--- REPORT FINALE ---");
  console.log(`✅ Prodotti in Italiano: ${results.it.length}`);
  console.log(`🇬🇧 Prodotti in Inglese: ${results.en.length}`);
  console.log(`🔄 Prodotti con Lingua Mista: ${results.mixed.length}`);

  if (results.en.length > 0) {
      console.log("\n📌 Esempi Prodotti in Inglese:");
      results.en.slice(0, 10).forEach(p => console.log(` - [${p.vendor}] ${p.title}`));
  }

  if (results.mixed.length > 0) {
      console.log("\n📌 Esempi Prodotti Misti:");
      results.mixed.slice(0, 10).forEach(p => console.log(` - [${p.vendor}] ${p.title}`));
  }
  
  const vendors = [...new Set([...results.en, ...results.mixed].map(p => p.vendor))];
  console.log(`\n⚠️ Brand maggiormente colpiti: ${vendors.join(", ")}`);
}

auditProducts().catch(console.error);
