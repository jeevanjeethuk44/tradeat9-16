# Groww Nifty Options Trading Bot

This Python script automates a specific options trading strategy for Nifty 50 on the Groww trading platform using the official Groww Trading API.

## 📜 Disclaimer

**Trading in the stock market, especially with automated bots, involves significant financial risk. You could lose money. This script is provided as-is, without any warranties. Use it at your own risk.**

- **This is not financial advice.** The trading strategy implemented is based on the user's specific request and may not be profitable.
- **You are responsible for all trades** placed by this bot and for any financial outcomes.
- **The Groww Trading API is a paid service.** You must have an active subscription to use this script.
- **Ensure you comply with Groww's API Terms of Service.** The use of automated scripts may be subject to specific rules and limitations.
- **Test thoroughly.** It is highly recommended to understand the code and monitor its behavior closely, especially during its first few runs.

---

## ✨ Features

- **Automated Trading:** Places trades automatically at a scheduled time.
- **Specific Strategy:** Buys both a Nifty 50 Call (CE) and Put (PE) option at 9:16 AM.
- **Premium Targeting:** Searches for options with a premium between ₹50 and ₹60.
- **Timed Exit:** Automatically sells the positions after 4 minutes, at 9:20 AM.
- **Weekday Scheduling:** The bot is configured to run only on trading days (Monday to Friday).
- **Robust Logging:** Logs all major actions, including API connections, trades placed, and errors, to both the console and a `trader.log` file.
- **Secure Credential Management:** Keeps your API keys safe by loading them from a `.env` file, not hardcoded in the script.

---

## 📋 Prerequisites

1.  A **Groww Demat and Trading Account**.
2.  An active **Groww Trading API Subscription**.
3.  **Python 3.9+** installed on your system.
4.  Your **Groww API Key** and **TOTP Secret Code**.

---

## ⚙️ Setup and Installation

Follow these steps to set up and run the trading bot on your local system.

### 1. Get the Code

Clone this repository or download the files (`trader.py`, `requirements.txt`, `README.md`) to a folder on your computer.

### 2. Create a Virtual Environment (Recommended)

It's a best practice to keep project dependencies isolated.

```bash
# Navigate to the project folder
cd /path/to/your/project

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

Install all the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Configure Your Credentials

The script uses a `.env` file to securely load your API credentials.

1.  Create a new file named `.env` in the same directory as `trader.py`.
2.  Add your Groww API Key and Secret Code to this file in the following format:

    ```env
    # .env file
    GROWW_API_KEY="your_actual_api_key_here"
    GROWW_SECRET_CODE="your_actual_totp_secret_code_here"
    ```

    **Important:**
    - Replace the placeholder text with your actual credentials.
    - The `SECRET_CODE` is the secret string you get when you generate the TOTP token on the Groww API page, **not** the 6-digit number.
    - Never share this file or commit it to a public repository.

---

## 🚀 How to Run the Bot

Once the setup is complete, you can start the bot.

1.  **Activate your virtual environment** (if you created one).
2.  **Run the script from your terminal:**

    ```bash
    python trader.py
    ```

3.  The script will start and display a message that it is running and waiting for the scheduled time.

    ```
    INFO:root:Trader script started. Waiting for scheduled time...
    INFO:root:Buy orders will be placed at 09:16 on weekdays.
    INFO:root:Sell orders will be placed at 09:20 on weekdays.
    ```

**Important:**
- The script needs to **run continuously** in a terminal window to work. If you close the terminal, the bot will stop.
- For long-term, reliable execution, consider running the script as a background service using a process manager like `pm2` (for Node.js, but can manage Python scripts too) or `systemd` (on Linux).
- Alternatively, you can use a `cron` job (macOS/Linux) or Task Scheduler (Windows) to run the script, but you would need to modify the script to execute once and exit, rather than running in a continuous loop. The current implementation with the `schedule` library is designed for a long-running process.

---

## 🛠️ How It Works

- **Scheduler:** The script uses the `schedule` library to trigger jobs at `09:16` and `09:20` every day from Monday to Friday.
- **State Management:** When the `place_trade_strategy` job runs at 9:16 AM, it places the buy orders and saves the order details (like `trading_symbol` and `lot_size`) into a file named `trades.json`.
- **Exit Logic:** At 9:20 AM, the `exit_trades` job reads the `trades.json` file to know exactly which positions to sell. After placing the sell orders, it deletes the file to ensure the trades are not sold again.
- **Logging:** All operations are logged to `trader.log`. Check this file to debug any issues or review the bot's past activity.
