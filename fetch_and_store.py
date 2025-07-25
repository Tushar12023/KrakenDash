import requests
import sqlite3
from datetime import datetime

DB_PATH = "kraken_data.db"

def fetch_ticker_data():
    url = "https://api.kraken.com/0/public/Ticker"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['result']

def store_data(data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for pair, stats in data.items():
        try:
            last_price = float(stats['c'][0])           
            volume_24h = float(stats['v'][1])          
            price_open = float(stats['o'])              
        except (KeyError, ValueError):
            continue 

        cur.execute('''
            INSERT INTO ticker_data (timestamp, pair, last_price, volume_24h, price_open)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.utcnow(), pair, last_price, volume_24h, price_open))

    conn.commit()
    conn.close()

def main():
    print("Fetching Kraken ticker data...")
    data = fetch_ticker_data()
    print(f"Fetched {len(data)} pairs. Storing into DB.")
    store_data(data)
    print("Data stored successfully.")

if __name__ == "__main__":
    main()
