import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;
const API_VERSION = "2024-10";

const query = `
{
  products(first: 50, reverse: true) {
    nodes {
      id
      title
      media(first: 10) {
        nodes {
          id
          mediaContentType
          status
          ... on MediaImage {
            image {
              url
            }
          }
        }
      }
    }
  }
}
`;

async function checkProductImages() {
  const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/${API_VERSION}/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN,
    },
    body: JSON.stringify({ query }),
  });

  const result: any = await response.json();
  const products = result.data.products.nodes;

  products.forEach((p: any) => {
    const images = p.media.nodes.filter((m: any) => m.mediaContentType === 'IMAGE');
    console.log(`[${p.title}] - Media totali: ${p.media.nodes.length} - Immagini: ${images.length}`);
    images.forEach((img: any, i: number) => {
        console.log(`  Img ${i+1}: ${img.status} - ${img.image?.url ? 'URL OK' : 'NO URL'}`);
    });
  });
}

checkProductImages().catch(console.error);
