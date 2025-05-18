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

def fetch_stock():
    try:
        print("🔍 Fetching stock data...")
        headers = {
            "User-Agent": "Mozilla/5.0 (SeedBot)",
            "Cache-Control": "no-cache"
        }
        res = requests.get(STOCK_URL, headers=headers, timeout=10)
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
    try:
        data = {
            "content": f"{ROLE_MENTION}\n{message}",
            "username": "Seed Notifier 🌱"
        }
        response = requests.post(WEBHOOK_URL, json=data, timeout=10)
        if response.status_code == 204:
            print("✅ Webhook sent")
        else:
            print(f"❌ Webhook failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"💥 Webhook error: {e}")

def seconds_until_next_restock(buffer=30):
    now = datetime.datetime.now()
    next_min = (now.minute // 5 + 1) * 5
    if next_min == 60:
        next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    else:
        next_time = now.replace(minute=next_min, second=0, microsecond=0)
    next_time += datetime.timedelta(seconds=buffer)
    return max((next_time - now).total_seconds(), 0)

def stock_loop():
    while True:
        try:
            wait = seconds_until_next_restock()
            print(f"⏳ Sleeping for {wait:.1f}s until next check...")
            time.sleep(wait)

            stock = fetch_stock()
            if not stock:
                print("⚠️ No stock fetched, retrying in 60s...")
                time.sleep(60)
                continue

            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            message = f"**🌱 Seed Stock ({timestamp}):**\n"
            for seed, qty in stock.items():
                message += f"- {seed}: {qty}\n"
            send_webhook(message)

        except Exception as e:
            print(f"⚠️ Loop error: {e}")
            time.sleep(30)

@app.route('/')
def home():
    return "🌿 Seed Notifier is running."

if __name__ == '__main__':
    threading.Thread(target=stock_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
