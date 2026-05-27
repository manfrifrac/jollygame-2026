import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function getCollectionProducts(id: string) {
  const query = `{
    collection(id: "${id}") {
      title
      products(first: 250) {
        nodes {
          title
          tags
        }
      }
    }
  }`;
  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!,
    },
    body: JSON.stringify({ query }),
  });
  const data = await res.json();
  const products = data.data?.collection?.products?.nodes || [];
  console.log(`\n📦 Prodotti in "${data.data?.collection?.title}":`);
  products.forEach((p: any) => console.log(` - ${p.title}`));
}

getCollectionProducts("gid://shopify/Collection/686008336732").catch(console.error);
