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
ROLE_MENTION = "<@&1372660035930296443>"

previous_stock = None


def fetch_stock():
    print("📦 Fetching stock at", datetime.datetime.now().strftime("%H:%M:%S"))

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SeedBot/1.0)",
        "Cache-Control": "no-cache"
    }

    try:
        response = requests.get(STOCK_URL, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error: Received status code {response.status_code}")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')

        seeds_section = soup.find('h2', string='SEEDS STOCK')
        if not seeds_section:
            print("❌ Couldn't find the 'SEEDS STOCK' header.")
            print("🔎 Here's part of the page:\n", soup.prettify()[:500])
            return {}

        stock = {}
        ul = seeds_section.find_next_sibling('ul')
        if not ul:
            print("❌ Couldn't find the stock <ul> list.")
            return {}

        for li in ul.find_all('li'):
            text = li.get_text(strip=True)
            if 'x' in text:
                name, qty = text.rsplit('x', 1)
                stock[name.strip()] = int(qty.strip())

        print("✅ Stock fetched:", stock)
        return stock

    except Exception as e:
        print(f"🔥 Exception while fetching stock: {e}")
        return {}


def send_webhook(message):
    data = {
        "content": f"{ROLE_MENTION}\n{message}",
        "username": "Seed Notifier 🌱"
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=data)
        if resp.status_code != 204:
            print(f"🚨 Webhook failed: {resp.status_code} - {resp.text}")
        else:
            print("✅ Webhook sent!")
    except Exception as e:
        print(f"🚨 Webhook error: {e}")


def seconds_until_next_5min_plus_buffer(buffer_seconds=7):
    now = datetime.datetime.now()
    minutes = now.minute
    next_5min = (minutes // 5 + 1) * 5
    if next_5min == 60:
        next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    else:
        next_time = now.replace(minute=next_5min, second=0, microsecond=0)

    next_time += datetime.timedelta(seconds=buffer_seconds)
    delta = (next_time - now).total_seconds()
    return delta if delta > 0 else 0


def stock_loop():
    global previous_stock

    while True:
        try:
            print("⏳ Waiting for next 5-min + buffer...")
            sleep_time = seconds_until_next_5min_plus_buffer()
            print(f"🛌 Sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)

            print("🔍 Time to check stock...")
            current_stock = fetch_stock()

            if not current_stock:
                print("⚠️ No stock data found, skipping webhook.")
                continue

            message = f"**🌱 Seed Stock Debug Check ({datetime.datetime.now().strftime('%H:%M:%S')}):**\n"
            for seed, qty in current_stock.items():
                message += f"- {seed}: {qty} in stock\n"

            send_webhook(message)
            previous_stock = current_stock

        except Exception as e:
            print(f"💥 Error in stock_loop: {e}")
            time.sleep(30)


@app.route('/')
def home():
    return "🌿 Seed Notifier is online and chillin (debug mode)"


if __name__ == '__main__':
    threading.Thread(target=stock_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
