import asyncio
from playwright.async_api import async_playwright
import json
import os
from dotenv import load_dotenv

load_dotenv()

USER = "jollygam@libero.it"
PASS = "AntoRiky61"

async def save_auth():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🔑 Per favore effettua il login manualmente nella finestra che si è aperta.")
        print("Spostati sulla dashboard e poi premi INVIO qui nel terminale.")
        
        await page.goto("https://pro.fluidra.com/it_it/customer/account/login/")
        
        # Aspettiamo l'utente
        input("Premi INVIO dopo che sei loggato correttamente...")
        
        # Salviamo lo stato
        await context.storage_state(path="fluidra_auth.json")
        print("✅ Sessione salvata in fluidra_auth.json")
        await browser.close()

if __name__ == "__main__":
    save_auth()
