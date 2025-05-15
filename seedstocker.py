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
ROLE_MENTION = "<@1372660035930296443>"  # replace with your actual role ID

previous_stock = None  # for tracking
last_sent_time = 0     # cooldown tracker (not used in debug mode)


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
    print("Fetched stock:", stock)
    return stock


def send_webhook(message):
    data = {
        "content": f"{ROLE_MENTION}\n{message}",
        "username": "Seed Notifier 🌱"
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=data)
        if resp.status_code != 204:
            print(f"Webhook failed: {resp.status_code} - {resp.text}")
        else:
            print("Webhook sent!")
    except Exception as e:
        print(f"Webhook error: {e}")


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
            print("Loop running... waiting for next interval ⏳")

            # Wait until next 5-min mark
            sleep_time = seconds_until_next_5min()
            print(f"Sleeping for {sleep_time:.1f} seconds to align with restock time")
            time.sleep(sleep_time)

            # Extra wait to make sure stock updated
            time.sleep(20)
            print("Checking stock after restock delay...")

            current_stock = fetch_stock()

            # DEBUG MODE: send every time
            message = "**🌱 Seed Stock Debug Check:**\n"
            for seed, qty in current_stock.items():
                message += f"- {seed}: {qty} in stock\n"

            send_webhook(message)

            previous_stock = current_stock

        except Exception as e:
            print(f"Error in stock_loop: {e}")
            time.sleep(30)  # chill if it crashes

@app.route('/')
def home():
    return "🌱 Seed Notifier is online (debug mode)"

if __name__ == '__main__':
    threading.Thread(target=stock_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
