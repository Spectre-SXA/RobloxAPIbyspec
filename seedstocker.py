import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask
import os
import datetime

app = Flask(__name__)

WEBHOOK_URL = 'https://discord.com/api/webhooks/1372652988807643391/R2ydruM68O9yGmWmM4iN1Fnp_qX7DztCn6oX3ll4eunwptc5JsHutIjG6AUM3hXGTlj9'
STOCK_URL = 'https://vulcanvalues.com/grow-a-garden/stock'
ROLE_MENTION = "<@&1372660035930296443>"  # Change this to your actual role ID

previous_stock = None


def fetch_stock():
    try:
        print("🔍 Fetching stock data (spoofing as legit browser)...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://google.com",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
        }

        res = requests.get(STOCK_URL, headers=headers, timeout=10)

        if "Access denied" in res.text or res.status_code == 403:
            print("🚫 BLOCKED as bot (403 or denial text)")
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        seeds_section = soup.find('h2', string='SEEDS STOCK')
        if not seeds_section:
            print("❌ Seeds header not found")
            return None

        ul = seeds_section.find_next_sibling('ul')
        if not ul:
            print("❌ Seeds list not found")
            return None

        stock = {}
        for li in ul.find_all('li'):
            text = li.get_text(strip=True)
            if 'x' in text:
                name, qty = text.rsplit('x', 1)
                stock[name.strip()] = int(qty.strip())

        print("✅ Stock:", stock)
        return stock

    except Exception as e:
        print(f"💥 Error fetching stock: {e}")
        return None


def send_webhook(message):
    data = {
        "content": f"{ROLE_MENTION}\n{message}",
        "username": "Seed Notifier 🌱"
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=data)
        if resp.status_code != 204:
            print(f"❗ Webhook failed: {resp.status_code} - {resp.text}")
        else:
            print("✅ Webhook sent!")
    except Exception as e:
        print(f"🚨 Webhook error: {e}")


def seconds_until_next_5min():
    now = datetime.datetime.now()
    minutes = now.minute
    next_5min = (minutes // 5 + 1) * 5
    if next_5min == 60:
        next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    else:
        next_time = now.replace(minute=next_5min, second=0, microsecond=0)
    delta = (next_time - now).total_seconds()
    return delta if delta > 0 else 0


def stock_loop():
    global previous_stock

    while True:
        try:
            print("⏳ Waiting for next 5-min restock interval...")
            sleep_time = seconds_until_next_5min()
            print(f"🛌 Sleeping {sleep_time:.1f} seconds to align with restock...")
            time.sleep(sleep_time)

            print("⏱️ Waiting extra 30 seconds for stock to fully update...")
            time.sleep(30)

            print("🔄 Fetching current stock...")
            current_stock = fetch_stock()

            if current_stock is None:
                print("⚠️ Could not fetch stock, skipping this loop.")
                continue

            # DEBUG: always send webhook
            message = "**🌱 Seed Stock Debug Check:**\n"
            for seed, qty in current_stock.items():
                message += f"- {seed}: {qty} in stock\n"

            send_webhook(message)
            previous_stock = current_stock

        except Exception as e:
            print(f"❌ Error in stock_loop: {e}")
            time.sleep(30)  # wait before retrying if crash


@app.route('/')
def home():
    return "🌱 Seed Notifier is online (debug mode)"


if __name__ == '__main__':
    threading.Thread(target=stock_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
