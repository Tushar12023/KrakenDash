import requests
import time
from collections import deque
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(filename='trending_coins.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Intervals for volume and trade analysis (in minutes)
INTERVALS = [5, 15, 30]

# Thresholds for trending detection
VOLUME_SPIKE_THRESHOLD = 50.0  # % volume increase
PRICE_CHANGE_THRESHOLD = 5.0   # % price change
TRADE_COUNT_SPIKE_THRESHOLD = 50.0  # % trade count increase

# Store history for each pair: (timestamp, volume, trades)
HISTORY = {}

def get_ticker_data():
    """Fetch ticker data for all trading pairs."""
    try:
        url = "https://api.kraken.com/0/public/Ticker"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('error'):
            raise Exception(f"API error: {data['error']}")
        return data['result']
    except requests.RequestException as e:
        logging.error(f"Failed to fetch ticker data: {e}")
        raise

def calculate_percent_change(current, past):
    """Calculate percentage change, handling zero past values."""
    if past == 0:
        return None
    return ((current - past) / past * 100

def initialize_history(pairs):
    """Initialize deque for each trading pair."""
    for pair in pairs:
        if pair not in HISTORY:
            HISTORY[pair] = deque(maxlen=max(INTERVALS) + 1)

def main():
    print("Starting trend detection for all Kraken pairs...")
    logging.info("Started trend detection program")

    try:
        # Get initial ticker data to fetch pairs
        ticker_data = get_ticker_data()
        pairs = list(ticker_data.keys())
        initialize_history(pairs)
        logging.info(f"Tracking {len(pairs)} trading pairs")
        print(f"Tracking {len(pairs)} trading pairs")

        while True:
            try:
                current_time = datetime.utcnow()
                ticker_data = get_ticker_data()
                trending_coins = []

                # Process each pair
                for pair in pairs:
                    if pair not in ticker_data:
                        logging.warning(f"Pair {pair} not in ticker data")
                        continue

                    # Extract metrics
                    current_volume = float(ticker_data[pair]['v'][1])  # 24h volume
                    current_price = float(ticker_data[pair]['c'][0])   # Last price
                    open_price = float(ticker_data[pair]['o'])         # 24h open price
                    trade_count = int(ticker_data[pair]['t'][1])       # 24h trades

                    # Calculate 24h price change
                    price_change = calculate_percent_change(current_price, open_price)

                    # Update history
                    HISTORY[pair].append((current_time, current_volume, trade_count))

                    # Check for trends over intervals
                    for interval in INTERVALS:
                        target_time = current_time - timedelta(minutes=interval)
                        past_volume = None
                        past_trades = None
                        min_time_diff = float('inf')

                        # Find closest past data point
                        for t, vol, trades in reversed(HISTORY[pair]):
                            time_diff = (current_time - t).total_seconds() / 60.0
                            if time_diff >= interval and time_diff < min_time_diff:
                                past_volume = vol
                                past_trades = trades
                                min_time_diff = time_diff

                        if past_volume is not None:
                            volume_change = calculate_percent_change(current_volume, past_volume)
                            trade_change = calculate_percent_change(trade_count, past_trades) if past_trades else None

                            # Flag as trending
                            is_trending = (
                                (volume_change is not None and volume_change > VOLUME_SPIKE_THRESHOLD) or
                                (price_change is not None and abs(price_change) > PRICE_CHANGE_THRESHOLD) or
                                (trade_change is not None and trade_change > TRADE_COUNT_SPIKE_THRESHOLD)
                            )

                            if is_trending:
                                trending_coins.append({
                                    'pair': pair,
                                    'volume_change': volume_change,
                                    'price_change': price_change,
                                    'trade_change': trade_change,
                                    'current_volume': current_volume,
                                    'current_price': current_price
                                })

                    # Log pair data
                    logging.info(f"{pair}: Volume={current_volume:.2f}, Price={current_price:.6f}, "
                                 f"PriceChange={price_change or 'N/A'}%, Trades={trade_count}")

                # Display trending coins
                if trending_coins:
                    print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}] Trending Coins:")
                    for coin in sorted(trending_coins, key=lambda x: x.get('volume_change', 0) or 0, reverse=True)[:10]:
                        print(f"{coin['pair']}: VolChange={coin['volume_change'] or 'N/A':.2f}%, "
                              f"PriceChange={coin['price_change'] or 'N/A':.2f}%, "
                              f"TradeChange={coin['trade_change'] or 'N/A':.2f}%, "
                              f"Volume={coin['current_volume']:.2f}, Price={coin['current_price']:.6f}")

                time.sleep(60)  # Poll every 60 seconds

            except KeyboardInterrupt:
                print("\nStopping trend detection.")
                logging.info("Program stopped by user")
                break
            except Exception as e:
                print(f"Error: {e}. Retrying in 60 seconds...")
                logging.error(f"Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    main()