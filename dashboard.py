import sqlite3
import streamlit as st
from datetime import datetime, timedelta

DB_FILE = "kraken_data.db"
TIME_WINDOWS = [1, 2, 3]  # In multiples of CRON_INTERVAL
CRON_INTERVAL = 15  # Workflow runs every 15 minutes
WINDOW = [w * CRON_INTERVAL for w in TIME_WINDOWS]  # [15, 30, 45]

# Streamlit Page Config
st.set_page_config(page_title="Kraken Market Dashboard", layout="wide")
st.title("📊 Kraken Market Dashboard")

# Auto-refresh every 30 seconds
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if (datetime.now() - st.session_state.last_refresh).total_seconds() > 30:
    st.session_state.last_refresh = datetime.now()
    st.rerun()

def get_latest_data():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT pair, volume_24h, last_price, MAX(timestamp)
        FROM ticker_data
        GROUP BY pair
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_volume_by_timestamp(pair, target_timestamp):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT volume_24h FROM ticker_data
        WHERE pair = ? AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (pair, target_timestamp))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_volume_change_by_offset(pair, offset_minutes):
    now = datetime.utcnow()
    target_time = now - timedelta(minutes=offset_minutes)
    latest_volume = get_volume_by_timestamp(pair, now)
    past_volume = get_volume_by_timestamp(pair, target_time)
    if latest_volume is None or past_volume is None or past_volume == 0:
        return None
    return ((latest_volume - past_volume) / past_volume) * 100

def get_price_by_timestamp(pair, target_timestamp):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT last_price FROM ticker_data
        WHERE pair = ? AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (pair, target_timestamp))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_price_change_24h(pair):
    now = datetime.utcnow()
    target_time = now - timedelta(hours=24)
    latest_price = get_price_by_timestamp(pair, now)
    past_price = get_price_by_timestamp(pair, target_time)
    if latest_price is None or past_price is None or past_price == 0:
        return None
    return ((latest_price - past_price) / past_price) * 100

def display_dashboard():
    data = get_latest_data()
    if not data:
        st.warning("No data available in the database.")
        return
    dashboard_data = []
    for pair, vol, price, ts in data:
        row = {
            "Asset": pair,
            "Last Price": round(price, 4),
            "% Change (24h)": get_price_change_24h(pair)
        }
        for offset_minutes in WINDOW:
            vol_change = get_volume_change_by_offset(pair, offset_minutes)
            row[f"Vol Δ ({offset_minutes}m)"] = vol_change
        dashboard_data.append(row)
    st.dataframe(
        dashboard_data,
        column_config={
            "Asset": "Trading Pair",
            "Last Price": st.column_config.NumberColumn(format="%.4f"),
            "% Change (24h)": st.column_config.NumberColumn(
                "% Change (24h)", format="%.2f %%", help="24-hour price percentage change"
            ),
            **{f"Vol Δ ({w}m)": st.column_config.NumberColumn(
                f"Vol Δ ({w}m)", format="%.2f %%", help=f"Volume change over last {w} minutes"
            ) for w in WINDOW}
        },
        hide_index=True,
        use_container_width=True
    )

if __name__ == "__main__":
    display_dashboard()