import os
import asyncio
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# === KONFIGURATION ===

SEARCH_URL = "https://stadtundland.de/wohnungssuche?district=Buckower+Felder&minRooms=3&maxRooms=3"

# In GitHub werden diese Werte als Umgebungsvariablen gesetzt
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def sende_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data, timeout=15)
        if not r.ok:
            print("Fehler beim Telegram-Versand:", r.text)
    except Exception as e:
        print("Telegram-Fehler:", e)


async def hole_anzahl_wohnungen() -> int:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Rufe Seite auf:", SEARCH_URL)
        await page.goto(SEARCH_URL, wait_until="networkidle")

        try:
            await page.wait_for_selector("text=Suchergebnis", timeout=15000)
        except PlaywrightTimeoutError:
            print("Konnte 'Suchergebnis' nicht finden.")
            await browser.close()
            return 0

        locator = page.locator("text=Suchergebnis").first
        raw_text = await locator.inner_text()
        print("Gefundener Text:", repr(raw_text))

        teile = raw_text.split()
        anzahl = 0
        for teil in teile:
            if teil.isdigit():
                anzahl = int(teil)
                break

        await browser.close()
        return anzahl


async def main():
    anzahl = await hole_anzahl_wohnungen()
    print("Anzahl Wohnungen:", anzahl)

    if anzahl > 0:
        text = f"Aktuelle Anzahl 3-Zimmer-Wohnungen in Buckower Felder: {anzahl}"
        sende_telegram(text)
    else:
        print("Keine Wohnungen gefunden, keine Nachricht gesendet.")


if __name__ == "__main__":
    asyncio.run(main())
