import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask
import os

app = Flask(__name__)

WEBHOOK_URL = 'https://discord.com/api/webhooks/1372652988807643391/R2ydruM68O9yGmWmM4iN1Fnp_qX7DztCn6oX3ll4eunwptc5JsHutIjG6AUM3hXGTlj9'
STOCK_URL = 'https://vulcanvalues.com/grow-a-garden/stock'
CHECK_INTERVAL = 300  # seconds (5 minutes)

previous_stock = None  # None to force first send

ROLE_MENTION = "<@&YOUR_ROLE_ID>"  # Replace YOUR_ROLE_ID with actual Discord role ID for @G-Seedrestock

def fetch_stock():
    response = requests.get(STOCK_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    seeds_section = soup.find('h2', string='SEEDS STOCK')
    if not seeds_section:
        return {}
    stock = {}
    for item in seeds_section.find_next_siblings('ul', limit=1):
        for li in item.find_all('li'):
            text = li.get_text(strip=True)
            if 'x' in text:
                name, qty = text.rsplit('x', 1)
                stock[name.strip()] = int(qty.strip())
    print("Fetched stock:", stock)  # Debug print
    return stock

def send_webhook(message):
    data = {
        "content": f"{ROLE_MENTION}\n{message}",
        "username": "Seed Notifier 🌱"
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=data)
        if resp.status_code != 204:
            print(f"Webhook returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Webhook error: {e}")

def stock_loop():
    global previous_stock
    while True:
        try:
            current_stock = fetch_stock()

            if previous_stock is None:
                # First check, always send webhook
                message = "**🌱 Grow a Garden Seed Stock Update (Initial):**\n"
                for seed, qty in current_stock.items():
                    message += f"- {seed}: {qty} in stock\n"
                send_webhook(message)
                previous_stock = current_stock
                print("Sent initial webhook.")
            elif current_stock != previous_stock:
                # Stock changed, send webhook
                message = "**🌱 Grow a Garden Seed Stock Update:**\n"
                for seed, qty in current_stock.items():
                    message += f"- {seed}: {qty} in stock\n"
                send_webhook(message)
                previous_stock = current_stock
                print("Stock changed! Sent webhook.")
            else:
                print("No change in stock.")

        except Exception as e:
            print(f"Error in stock_loop: {e}")

        time.sleep(CHECK_INTERVAL)

@app.route('/')
def home():
    return "🌱 Seed Notifier is online and running!"

if __name__ == '__main__':
    threading.Thread(target=stock_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
