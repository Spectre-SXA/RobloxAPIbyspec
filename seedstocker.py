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

previous_stock = None  # None to force first send

ROLE_MENTION = "<@&1372660035930296443>"  # Replace YOUR_ROLE_ID with your Discord role ID for @G-Seedrestock

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

def seconds_until_next_5min():
    now = datetime.datetime.now()
    minutes = now.minute
    next_5min = (minutes // 5 + 1) * 5
    if next_5min == 60:
        # next hour
        next_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    else:
        next_time = now.replace(minute=next_5min, second=0, microsecond=0)
    delta = (next_time - now).total_seconds()
    return delta if delta > 0 else 0

def stock_loop():
    global previous_stock, last_sent_time
    while True:
        try:
            # Wait till 5-min mark first
            sleep_time = seconds_until_next_5min()
            print(f"Sleeping for {sleep_time} seconds until next restock check.")
            time.sleep(sleep_time)

            # Then wait extra 20 seconds to make sure restock happened
            delay_after_restock = 20
            print(f"Waiting additional {delay_after_restock} seconds to let restock settle.")
            time.sleep(delay_after_restock)

            current_stock = fetch_stock()
            now = time.time()

            if previous_stock is None:
                message = "**🌱 Grow a Garden Seed Stock Update (Initial):**\n"
                for seed, qty in current_stock.items():
                    message += f"- {seed}: {qty} in stock\n"
                send_webhook(message)
                previous_stock = current_stock
                last_sent_time = now
                print("Sent initial webhook.")

            elif current_stock != previous_stock:
                if now - last_sent_time >= COOLDOWN_SECONDS:
                    message = "**🌱 Grow a Garden Seed Stock Update:**\n"
                    for seed, qty in current_stock.items():
                        message += f"- {seed}: {qty} in stock\n"
                    send_webhook(message)
                    previous_stock = current_stock
                    last_sent_time = now
                    print("Stock changed! Sent webhook.")
                else:
                    print(f"Stock changed but cooldown active. Not sending yet. Cooldown left: {COOLDOWN_SECONDS - (now - last_sent_time):.1f}s")
            else:
                print("No change in stock.")

        except Exception as e:
            print(f"Error in stock_loop: {e}")


@app.route('/')
def home():
    return "🌱 Seed Notifier is online and running!"

if __name__ == '__main__':
    threading.Thread(target=stock_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
