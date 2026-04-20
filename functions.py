import requests
import csv
import re
import os

class PriceError(Exception):
    pass


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
    url = "https://open.er-api.com/v6/latest/USD"
    r = requests.get(url)
    r.raise_for_status()

    data = r.json()

    if data["result"] != "success":
        raise Exception(f"API error: {data}")

    return data["rates"]["EUR"]
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
        
        if "cardmarket" in data and data["cardmarket"]:
            return data["cardmarket"][-1][1] / 100, "LTS"
        else:
            raise PriceError(f"No Cardmarket price for: {name}")        

    # fallback
    if name in cm_table:

        url = f"https://app.getcollectr.com/explore/product/{cm_table[name]}"
        price = get_price_collectr(url) 

        if price is None:
            raise PriceError(f"Collectr price not found for: {name}")
            
        return round(price * rate, 2), "CTR"

    raise PriceError(f"Card ID + mapping not found for: {name}")

def selling(TOKEN,CHAT_ID):
    rate = get_rate() 
    rows = []
    with open("Card_List.csv", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        reader = [row for row in reader if len(row) > 1 and row[1].strip()]
    
        cm_table = load_cardmarket_table("mapping.csv")
    
        for row in reader:
            name = row[1]
            anzahl = int(row[2])
    
            if anzahl == 0:
                continue
            try:
                price, site = get_price(name, cm_table, rate)
            except PriceError:
                continue
    
            if price > 2.00:
                rows.append((name, f"{price:.2f}€", str(anzahl), site))
    
    if not rows:
        send_telegram("No cards above 2€ today.", TOKEN, CHAT_ID)
        return
    
    name_w = max(len(r[0]) for r in rows)
    price_w = max(len(r[1]) for r in rows)
    qty_w = max(len(r[2]) for r in rows)
    
    text = "📈 Cards worth more than 2€ today\n\n"
    text += "```\n"
    
    # header
    text += f"{'Name':<{name_w}} | {'Price':>{price_w}} | {'N':>{qty_w}} | Site\n"
    
    # separator line
    text += f"{'-'*name_w}-+-{'-'*price_w}-+-{'-'*qty_w}-+----\n"
    
    # rows
    for name, price, qty, site in rows:
        text += f"{name:<{name_w}} | {price:>{price_w}} | {qty:>{qty_w}} | {site}\n"
    
    text += "```\n"
    text += "\nThat's it for today."
    
    send_telegram(text, TOKEN, CHAT_ID)

######

### TELEGRAM ###
def send_telegram(message,TOKEN,CHAT_ID):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    requests.post(url, data=data)

if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]
    CHAT_ID = os.environ["CHAT_ID"]
    selling(TOKEN,CHAT_ID)
