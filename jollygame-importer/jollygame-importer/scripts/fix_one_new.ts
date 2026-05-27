import dotenv from "dotenv";
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function fixOne() {
  const productId = "gid://shopify/Product/15597334692188";
  const variantId = "gid://shopify/ProductVariant/57707533140316";
  const sku = "KITPROV7388N";
  const price = "4707.1";

  const mutation = `
  mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
    productVariantsBulkUpdate(productId: $productId, variants: $variants) {
      product { id }
      productVariants { id sku price }
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
        productId, 
        variants: [{ id: variantId, sku, price }] 
      } 
    })
  });

  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));
}

fixOne().catch(console.error);
