import sqlite3

conn = sqlite3.connect("kraken_data.db")
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS ticker_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    pair TEXT NOT NULL,
    last_price REAL,
    volume_24h REAL,
    price_open REAL
)
''')

conn.commit()
conn.close()
