import requests
from bs4 import BeautifulSoup
import time

WEBHOOK_URL = 'https://discord.com/api/webhooks/your_webhook_id/your_token'
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

if __name__ == "__main__":
    main()
