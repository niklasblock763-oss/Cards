import requests
import csv
import re
import os


### COLLECTR ###
def get_price_collectr(card_url):
    headers = { "User-Agent": "Mozilla/5.0", "Accept": "application/json", "Origin": "https://app.getcollectr.com", "Referer": "https://app.getcollectr.com/" }
    r = requests.get(card_url, headers=headers) 
    html = r.text
    match = re.search(r'market_price.*?(\d+.\d+)', html)
    if match: 
        price = float(match.group(1)) 
        return price 
    
def get_rate():
    url = "https://api-v2.getcollectr.com/data/exchange-rates"
    headers = { "User-Agent": "Mozilla/5.0", "Accept": "application/json", "Origin": "https://app.getcollectr.com", "Referer": "https://app.getcollectr.com/" }
    r = requests.get(url, headers=headers) 
    data = r.json()
    rate = float(next(i["rate"] for i in data["data"] if i["currency"] == "EUR"))
    return rate
######

### LIMITLESS ### 
def get_card_id(card_url):

    r = requests.get(card_url)
    html = r.text

    match = re.search(r'cardId\s*=\s*(\d+)', html)
    if match:
        return match.group(1)

    return None
######

### HELPER ###
def load_cardmarket_table(path):

    mapping = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            mapping[row["limitless_name"]] = row["collectr_name"]

    return mapping

def get_url(name):
    return f"https://onepiece.limitlesstcg.com/cards/{name}"
######

### COMPUTING PRICES ###
def get_price(name, cm_table, rate):

    card_url = get_url(name)
    card_id = get_card_id(card_url)

    if card_id is not None:

        api_url = f"https://onepiece.limitlesstcg.com/api/cards/{card_id}/prices"

        r = requests.get(api_url)
        data = r.json()

        if data["cardmarket"]:
            return data["cardmarket"][-1][1] / 100

    # fallback
    if name in cm_table:

        url = f"https://app.getcollectr.com/explore/product/{cm_table[name]}"
        price = get_price_collectr(url) 
        
        return round(price * rate, 2)

    return None

def selling(TOKEN,CHAT_ID):
    rate = get_rate()
    text = "These Cards are more worth than 2€ today:\n\n"
    with open("Card_List.csv", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        reader = [row for row in reader if len(row) > 1 and row[1].strip()]

        cm_table = load_cardmarket_table("mapping.csv")

        for row in reader:

            name = row[1]
            anzahl = int(row[2])

            if anzahl == 0:
                continue

            price = get_price(name, cm_table, rate)


            if price is None:
                print("Missing mapping:", name)
                continue


            if price > 2.00:
                #name = get_name(name)
                price =  round(price,2) 
                price = f"{price:.2f}"
                text += f"{name} -> {price}€ -> {anzahl}\n"
    text += f"\nThat's it for today."
    send_telegram(text,TOKEN,CHAT_ID)
######

### TELEGRAM ###
def send_telegram(message,TOKEN,CHAT_ID):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]
    CHAT_ID = os.environ["CHAT_ID"]
    selling(TOKEN,CHAT_ID)
