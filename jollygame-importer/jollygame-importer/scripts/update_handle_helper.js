
import dotenv from 'dotenv';
import fs from 'fs';
dotenv.config();

const SHOP_DOMAIN = process.env.SHOP_DOMAIN;
const ACCESS_TOKEN = process.env.SHOPIFY_ACCESS_TOKEN;

async function updateProductHandle(productId, newHandle) {
  const query = `
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product {
          id
          handle
        }
        userErrors {
          field
          message
        }
      }
    }
  `;

  const variables = {
    input: {
      id: productId,
      handle: newHandle
    }
  };

  const response = await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Access-Token': ACCESS_TOKEN,
    },
    body: JSON.stringify({ query, variables }),
  });

  const result = await response.json();
  return result.data.productUpdate;
}

// Example usage
async function run() {
  // Update Sumatra as a test if needed
  // const sumatraId = "gid://shopify/Product/15527821082972";
  // const newHandle = "kpeov5027-sumatra-piscine-interrate-in-acciaio-dim-500x300-altezza-120";
  // const res = await updateProductHandle(sumatraId, newHandle);
  // console.log(res);
}

// Export for use in other scripts
export { updateProductHandle };
