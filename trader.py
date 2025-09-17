import os
import schedule
import time
import datetime
import json
import logging
import pandas as pd
import numpy as np
import pyotp
from growwapi import GrowwAPI
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv("GROWW_API_KEY")
SECRET_CODE = os.getenv("GROWW_SECRET_CODE")

# Trading parameters
PREMIUM_LOWER_BOUND = 50
PREMIUM_UPPER_BOUND = 60
TARGET_PREMIUM = (PREMIUM_LOWER_BOUND + PREMIUM_UPPER_BOUND) / 2
TRADE_TIME = "09:16"
EXIT_TIME = "09:20"

# File to store state of open trades
STATE_FILE = "trades.json"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trader.log"),
        logging.StreamHandler()
    ]
)

def connect_api():
    """Establishes a connection to the Groww API using TOTP."""
    logging.info("Attempting to connect to Groww API...")
    try:
        if not API_KEY or not SECRET_CODE:
            logging.error("API_KEY or SECRET_CODE not found in .env file.")
            raise ValueError("API credentials not set.")

        totp_gen = pyotp.TOTP(SECRET_CODE)
        totp = totp_gen.now()

        access_token = GrowwAPI.get_access_token(api_key=API_KEY, totp=totp)
        groww = GrowwAPI(access_token)

        logging.info("Successfully connected to Groww API.")
        return groww
    except Exception as e:
        logging.error(f"Failed to connect to Groww API: {e}")
        return None

def fetch_and_filter_instruments(groww):
    """Fetches all instruments and filters for nearest expiry Nifty FNO."""
    logging.info("Fetching and filtering instruments...")
    try:
        instruments_df = groww.get_all_instruments()
        if instruments_df is None or instruments_df.empty:
            logging.error("Failed to fetch instruments.")
            return None

        # Filter for NIFTY FNO instruments
        nifty_fno = instruments_df[
            (instruments_df['underlying_symbol'] == 'NIFTY') &
            (instruments_df['segment'] == 'FNO') &
            (instruments_df['instrument_type'].isin(['PE', 'CE']))
        ].copy()

        # Find the nearest expiry date
        nifty_fno['expiry_date'] = pd.to_datetime(nifty_fno['expiry_date'])
        today = datetime.datetime.now().date()

        future_expiries = nifty_fno[nifty_fno['expiry_date'].dt.date >= today]['expiry_date']
        if future_expiries.empty:
            logging.warning("No future expiry dates found for Nifty options.")
            return None

        nearest_expiry = future_expiries.min()
        logging.info(f"Nearest Nifty expiry date found: {nearest_expiry.date()}")

        # Filter for the nearest expiry
        weekly_options = nifty_fno[nifty_fno['expiry_date'] == nearest_expiry]
        return weekly_options

    except Exception as e:
        logging.error(f"An error occurred while fetching instruments: {e}")
        return None

def find_best_option(options_df, ltp_data):
    """Finds the option with premium closest to the target."""
    best_option = None
    min_diff = float('inf')

    for index, row in options_df.iterrows():
        symbol = row['trading_symbol']
        ltp_key = f"NSE_{symbol}"

        if ltp_key in ltp_data and ltp_data[ltp_key] is not None:
            ltp = ltp_data[ltp_key]
            if PREMIUM_LOWER_BOUND <= ltp <= PREMIUM_UPPER_BOUND:
                diff = abs(ltp - TARGET_PREMIUM)
                if diff < min_diff:
                    min_diff = diff
                    best_option = row
                    best_option['ltp'] = ltp

    return best_option

def place_trade_strategy():
    """The main logic to find and buy CE and PE options."""
    logging.info("--- Starting 9:16 AM trade strategy ---")
    groww = connect_api()
    if not groww:
        return

    options = fetch_and_filter_instruments(groww)
    if options is None or options.empty:
        logging.warning("Could not retrieve Nifty options. Aborting trade.")
        return

    ce_options = options[options['instrument_type'] == 'CE']
    pe_options = options[options['instrument_type'] == 'PE']

    # Get LTP for all relevant options in batches
    all_symbols = [f"NSE_{s}" for s in options['trading_symbol']]
    ltp_data = {}
    try:
        # The API supports fetching multiple symbols at once
        ltp_response = groww.get_ltp(segment=groww.SEGMENT_FNO, exchange_trading_symbols=tuple(all_symbols))
        if ltp_response:
            ltp_data.update(ltp_response)
        logging.info(f"Fetched LTP for {len(ltp_data)} options.")
    except Exception as e:
        logging.error(f"Could not fetch LTP data: {e}")
        return

    # Find best CE and PE options
    selected_ce = find_best_option(ce_options, ltp_data)
    selected_pe = find_best_option(pe_options, ltp_data)

    trades_to_place = []
    if selected_ce is not None:
        logging.info(f"Selected CE: {selected_ce['trading_symbol']} with LTP: {selected_ce['ltp']}")
        trades_to_place.append(selected_ce)
    else:
        logging.warning("No suitable CE option found in the desired premium range.")

    if selected_pe is not None:
        logging.info(f"Selected PE: {selected_pe['trading_symbol']} with LTP: {selected_pe['ltp']}")
        trades_to_place.append(selected_pe)
    else:
        logging.warning("No suitable PE option found in the desired premium range.")

    if not trades_to_place:
        logging.info("No trades to place. Ending strategy.")
        return

    # Place orders
    placed_trades = []
    for trade in trades_to_place:
        try:
            logging.info(f"Placing BUY order for {trade['trading_symbol']}...")
            order_response = groww.place_order(
                trading_symbol=trade['trading_symbol'],
                quantity=int(trade['lot_size']),
                validity=groww.VALIDITY_DAY,
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                product=groww.PRODUCT_INTRA,
                order_type=groww.ORDER_TYPE_MARKET,
                transaction_type=groww.TRANSACTION_TYPE_BUY
            )
            logging.info(f"Order placement response for {trade['trading_symbol']}: {order_response}")
            if order_response and order_response.get('groww_order_id'):
                placed_trades.append({
                    'trading_symbol': trade['trading_symbol'],
                    'lot_size': int(trade['lot_size']),
                    'groww_order_id': order_response['groww_order_id']
                })
        except Exception as e:
            logging.error(f"Failed to place BUY order for {trade['trading_symbol']}: {e}")

    # Save state for exit job
    if placed_trades:
        with open(STATE_FILE, 'w') as f:
            json.dump(placed_trades, f)
        logging.info(f"Successfully placed {len(placed_trades)} trades. State saved to {STATE_FILE}.")

def exit_trades():
    """The logic to sell all open positions from the state file."""
    logging.info("--- Starting 9:20 AM exit strategy ---")
    if not os.path.exists(STATE_FILE):
        logging.info("No state file found. No trades to exit.")
        return

    with open(STATE_FILE, 'r') as f:
        trades_to_exit = json.load(f)

    if not trades_to_exit:
        logging.info("State file is empty. No trades to exit.")
        os.remove(STATE_FILE)
        return

    groww = connect_api()
    if not groww:
        return

    for trade in trades_to_exit:
        try:
            logging.info(f"Placing SELL order for {trade['trading_symbol']}...")
            order_response = groww.place_order(
                trading_symbol=trade['trading_symbol'],
                quantity=trade['lot_size'],
                validity=groww.VALIDITY_DAY,
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                product=groww.PRODUCT_INTRA,
                order_type=groww.ORDER_TYPE_MARKET,
                transaction_type=groww.TRANSACTION_TYPE_SELL
            )
            logging.info(f"Exit order placement response for {trade['trading_symbol']}: {order_response}")
        except Exception as e:
            logging.error(f"Failed to place SELL order for {trade['trading_symbol']}: {e}")

    # Clean up state file after attempting to exit all trades
    os.remove(STATE_FILE)
    logging.info(f"Exit process complete. State file '{STATE_FILE}' removed.")


if __name__ == "__main__":
    logging.info("Trader script started. Waiting for scheduled time...")
    logging.info(f"Buy orders will be placed at {TRADE_TIME} on weekdays.")
    logging.info(f"Sell orders will be placed at {EXIT_TIME} on weekdays.")

    # Schedule the jobs
    for day in [schedule.every().monday, schedule.every().tuesday, schedule.every().wednesday, schedule.every().thursday, schedule.every().friday]:
        day.at(TRADE_TIME).do(place_trade_strategy)
        day.at(EXIT_TIME).do(exit_trades)

    # For testing purposes, you can uncomment these lines to run the jobs quickly
    # schedule.every(1).minutes.do(place_trade_strategy)
    # schedule.every(2).minutes.do(exit_trades)

    while True:
        schedule.run_pending()
        time.sleep(1)
