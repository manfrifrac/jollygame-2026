import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function testAddVariant() {
  const productId = "gid://shopify/Product/15597334692188";
  
  const mutation = `
  mutation productVariantsBulkCreate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
    productVariantsBulkCreate(productId: $productId, variants: $variants) {
      productVariants { id title }
      userErrors { field message }
    }
  }
  `;

  const res = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": ACCESS_TOKEN!
    },
    body: JSON.stringify({
      query: mutation,
      variables: {
        productId: productId,
        variants: [
          {
            inventoryItem: {
              sku: "TEST-SKU-DIM"
            },
            price: "100.00",
            optionValues: [{ name: "730x375", optionName: "Misura" }]
          }
        ]
      }
    })
  });

  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));
}

testAddVariant().catch(console.error);
