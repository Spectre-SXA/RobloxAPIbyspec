import requests
from bs4 import BeautifulSoup
import time

WEBHOOK_URL = 'https://discord.com/api/webhooks/1372652988807643391/R2ydruM68O9yGmWmM4iN1Fnp_qX7DztCn6oX3ll4eunwptc5JsHutIjG6AUM3hXGTlj9'
STOCK_URL = 'https://vulcanvalues.com/grow-a-garden/stock'
CHECK_INTERVAL = 300  # Check every 5 minutes

previous_stock = {}

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
    return stock

def send_webhook(message):
    data = {
        "content": message,
        "username": "Seed Notifier 🌱"
    }
    requests.post(WEBHOOK_URL, json=data)

def main():
    global previous_stock
    while True:
        try:
            current_stock = fetch_stock()
            if current_stock != previous_stock:
                message = "**🌱 Grow a Garden Seed Stock Update:**\n"
                for seed, qty in current_stock.items():
                    message += f"- {seed}: {qty} in stock\n"
                send_webhook(message)
                previous_stock = current_stock
            else:
                print("No change in seed stock.")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(CHECK_INTERVAL)

import os

if __name__ == '__main__':
    threading.Thread(target=stock_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))  # Use Render's port or default to 10000
    app.run(host='0.0.0.0', port=port)
