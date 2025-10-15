import dontshare as d
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import os

# CONFIG
TOKEN_ADDRESS = "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump"
KEY = d.birdeye_api_key
START_DATE = "01-20-2024"  # mm-dd-yyyy
END_DATE = "11-27-2027"    # mm-dd-yyyy
MIN_TRADE_SIZE = 3000      # Minimum trade size in USD
MAX_TRADE_SIZE = 10000000  # Maximum trade size in USD
OUTPUT_FOLDER = "data/"
SORT_TYPE = "asc"  # Can be "asc" or "desc"

# Convert date strings to datetime objects
START_TIME = datetime.strptime(START_DATE, "%m-%d-%Y")
END_TIME = datetime.strptime(END_DATE, "%m-%d-%Y") + timedelta(days=1) - timedelta(seconds=1)

print(f"Fetching trades for {TOKEN_ADDRESS} from {START_DATE} to {END_DATE}")
print(f"Trade size filter: ${MIN_TRADE_SIZE} - ${MAX_TRADE_SIZE}")
print(f"Start time: {START_TIME}")
print(f"End time: {END_TIME}")

# Function to get trades from the API
def get_trades(offset=0, sort_type=SORT_TYPE):
    url = f"https://public-api.birdeye.so/defi/txs/token?address={TOKEN_ADDRESS}&offset={offset}&limit=50&tx_type=swap&sort_type={sort_type}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": KEY
    }
    print(f"Fetching trades with offset {offset}...")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        time.sleep(5)
        return None

# Function to process trades
def process_trades(trades):
    processed_trades = []
    trades_processed = 0
    trades_written = 0
    for trade in trades:
        trades_processed += 1
        trade_time = datetime.fromtimestamp(trade['blockUnixTime'])
        quote = trade.get('quote', {})
        base = trade.get('base', {})
        try:
            ui_amount = float(quote.get('uiAmount', 0))
            nearest_price = quote.get('nearestPrice')
            if nearest_price is None:
                raise ValueError("nearestPrice is None")
            nearest_price = float(nearest_price)
            trade_size_usd = ui_amount * nearest_price
        except (TypeError, ValueError) as e:
            print(f"Error calculating trade size for trade at {trade_time}: {e}")
            print(f"Quote data: {quote}")
            continue
        print(f"Processing trade: {trade_time} | Size: ${trade_size_usd:.2f}")
    return processed_trades, True  # Placeholder for `continue_processing` flag

# Main search function
def start_search():
    timer_start = time.time()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_file = os.path.join(OUTPUT_FOLDER, f"{TOKEN_ADDRESS}.csv")
    print(f"Output file set to: {output_file}")

    all_trades = []
    offset = 0
    total_trades_processed = 0
    total_trades_written = 0
    found_trades_in_range = False
    consecutive_empty_batches = 0
    consecutive_errors = 0
    max_empty_batches = 3
    max_consecutive_errors = 3

    while True:
        data = get_trades(offset, sort_type=SORT_TYPE)
        if not data:
            consecutive_errors += 1
            print(f"API error occurred. Error count: {consecutive_errors}")
            if consecutive_errors >= max_consecutive_errors:
                print(f"Reached {max_consecutive_errors} consecutive errors. Stopping.")
                break
            offset += 50
            continue
        else:
            consecutive_errors = 0

        trades = data.get('data', {}).get('items', [])
        if not trades:
            consecutive_empty_batches += 1
            print(f"No trades in this batch. Empty batch count: {consecutive_empty_batches}")
            if consecutive_empty_batches >= max_empty_batches:
                print(f"Reached {max_empty_batches} consecutive empty batches. Stopping.")
                break
        else:
            consecutive_empty_batches = 0

        print(f"Processing batch of {len(trades)} trades...")
        processed_trades, continue_processing = process_trades(trades)
        all_trades.extend(processed_trades)

        if processed_trades:
            found_trades_in_range = True

        if found_trades_in_range and not continue_processing:
            print("Reached end of trades in specified date range")
            break

        total_trades_processed += len(trades)
        total_trades_written += len(processed_trades)

        offset += 50
        if offset > 100000:  # Add a safety limit
            print("Reached maximum offset. Stopping to prevent potential issues.")
            break

        print(f"Total trades processed: {total_trades_processed}, written: {total_trades_written}")
        print("Waiting 1.001 seconds before next request...")
        time.sleep(1.001)

    df = pd.DataFrame(all_trades)
    if not df.empty:
        df.to_csv(output_file, index=False)
        print(f"Trades saved to {output_file}")
    else:
        print("No trades found within the specified date range and trade size limits.")

    print(f"Total trades processed: {total_trades_processed}")
    print(f"Total trades written: {len(df)}")

    timer_end = time.time()
    duration = timer_end - timer_start
    print(f"Total execution time: {duration:.2f} seconds")
    print(f"Token address: {TOKEN_ADDRESS}")

if __name__ == "__main__":
    start_search()
