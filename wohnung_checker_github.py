import os
import asyncio
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# === KONFIGURATION ===

SEARCH_URL = "https://stadtundland.de/wohnungssuche?district=Buckower+Felder&minRooms=3&maxRooms=3"

# In GitHub werden diese Werte als Umgebungsvariablen gesetzt
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

LAST_COUNT_FILE = "last_count.txt"


def sende_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data, timeout=15)
        if not r.ok:
            print("Fehler beim Telegram-Versand:", r.text)
    except Exception as e:
        print("Telegram-Fehler:", e)


def lade_letzte_anzahl() -> int | None:
    if not os.path.exists(LAST_COUNT_FILE):
        return None
    try:
        with open(LAST_COUNT_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None


def speichere_anzahl(anzahl: int) -> None:
    with open(LAST_COUNT_FILE, "w", encoding="utf-8") as f:
        f.write(str(anzahl))


async def hole_anzahl_wohnungen() -> int:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Rufe Seite auf:", SEARCH_URL)
        await page.goto(SEARCH_URL, wait_until="networkidle")

        try:
            await page.wait_for_selector("text=Suchergebnis", timeout=15000)
        except TimeoutError as e:
            # Wenn du magst, genauer loggen
            print("Konnte 'Suchergebnis' nicht finden:", e)
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
    alte_anzahl = lade_letzte_anzahl()
    neue_anzahl = await hole_anzahl_wohnungen()

    print(f"Alte Anzahl: {alte_anzahl}, neue Anzahl: {neue_anzahl}")

    if alte_anzahl is None or neue_anzahl != alte_anzahl:
        # NUR HIER wird gesendet
        text = f"Aktuelle Anzahl 3-Zimmer-Wohnungen in Buckower Felder: {neue_anzahl}"
        print("Anzahl hat sich geändert -> Telegram:", text)
        sende_telegram(text)
        speichere_anzahl(neue_anzahl)
    else:
        print("Keine Änderung -> keine Telegram-Nachricht.")


if __name__ == "__main__":
    asyncio.run(main())
