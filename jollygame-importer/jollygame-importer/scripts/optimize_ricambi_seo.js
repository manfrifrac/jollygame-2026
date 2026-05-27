import dotenv from 'dotenv';
dotenv.config();

async function run() {
  let allProducts = [];
  let cursor = null;
  let hasNextPage = true;

  console.log("Fetching all products for final optimization...");

  while (hasNextPage) {
    const query = `{
      products(first: 250, after: ${cursor ? `"${cursor}"` : "null"}) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          title
          productType
          vendor
          descriptionHtml
          tags
          variants(first: 1) {
            nodes {
              sku
              barcode
            }
          }
        }
      }
    }`;

    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query }),
    });

    const result = await response.json();
    if (result.errors) {
      console.error(result.errors);
      break;
    }
    const { nodes, pageInfo } = result.data.products;
    allProducts.push(...nodes);
    hasNextPage = pageInfo.hasNextPage;
    cursor = pageInfo.endCursor;
  }

  const ricambiKeywords = ["ricambio", "parti di", "parti di ricambio", "liner", "cartuccia", "tubo", "raccordo", "adattatore", "guarnizione", "elettrodi", "valvola"];

  const toUpdate = allProducts.filter(p => 
    ricambiKeywords.some(kw => p.title.toLowerCase().includes(kw)) ||
    (p.productType && p.productType.toLowerCase().includes("ricambio")) ||
    (p.productType && p.productType.toLowerCase().includes("accessori"))
  );

  console.log(`Updating ${toUpdate.length} products to 'Ricambio' type and adding SEO headers...`);

  const mutation = `
  mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
      product {
        id
        title
      }
      userErrors {
        field
        message
      }
    }
  }
  `;

  for (const p of toUpdate) {
    const sku = p.variants.nodes[0]?.sku || "";
    const ean = p.variants.nodes[0]?.barcode || "";
    const codeString = [sku, ean].filter(Boolean).join(" / ");
    
    let newDescription = p.descriptionHtml;
    const seoHeader = `<h3>Codice Produttore: ${codeString}</h3>`;
    
    if (codeString && !newDescription.includes(seoHeader)) {
      newDescription = seoHeader + newDescription;
    }

    const input = {
      id: p.id,
      productType: "Ricambio",
      descriptionHtml: newDescription,
      tags: [...new Set([...(p.tags || []), "Tipo: Ricambio"])]
    };

    const response = await fetch(`https://${process.env.SHOP_DOMAIN}/admin/api/2024-10/graphql.json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': process.env.SHOPIFY_ACCESS_TOKEN,
      },
      body: JSON.stringify({ query: mutation, variables: { input } }),
    });

    const result = await response.json();
    if (result.data?.productUpdate?.userErrors.length > 0) {
      console.error(`Error updating ${p.title}:`, result.data.productUpdate.userErrors);
    } else {
      console.log(`Updated: ${p.title}`);
    }
  }
}

run().catch(console.error);
