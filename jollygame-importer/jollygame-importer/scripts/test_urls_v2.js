import fetch from 'node-fetch';

async function testUrl(url) {
  try {
    const response = await fetch(url, { redirect: 'manual' });
    console.log(`URL: ${url} -> Status: ${response.status}`);
  } catch (error) {
    console.error(`URL: ${url} -> Error: ${error.message}`);
  }
}

async function run() {
  await testUrl('https://jollygamepiscine.myshopify.com/pages/brand-ricambi/zodiac');
  await testUrl('https://jollygamepiscine.myshopify.com/pages/brand_ricambi/zodiac');
  await testUrl('https://jollygamepiscine.myshopify.com/pages/nome/zodiac');
  await testUrl('https://jollygamepiscine.myshopify.com/pages/zodiac');
  await testUrl('https://jollygame.it/pages/nome/zodiac');
}

run();