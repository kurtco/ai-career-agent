"""
Script para generar data/session_state.json manualmente.
Abre un navegador visible, espera a que te loguees en LinkedIn,
y guarda el estado de sesión para el scraper.
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def main() -> None:
    output = Path("data/session_state.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        print("Loguéate manualmente en LinkedIn. Cuando termines, presiona Enter en la terminal...")
        input()
        await context.storage_state(path=str(output))
        print(f"Sesión guardada en {output}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
