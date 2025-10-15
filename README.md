# AltcoinCopySniper
This project provides two Python scripts, BuyerFinder.py and sniper.py, designed to fetch and analyze cryptocurrency trade data using the Birdeye API. The scripts focus on retrieving trade information for a specified token, identifying early buyers, and analyzing their trading behavior and profitability.
Features

BuyerFinder.py: Fetches trade data for a specific token within a defined date range and trade size, processes it, and saves the results to a CSV file.
sniper.py: Identifies early buyers of a token, analyzes their wallet creation times, calculates their realized profit/loss (PnL), and checks for interactions between buyers.
Both scripts use the Birdeye API to access real-time Solana blockchain data and include error handling and rate-limiting considerations.
Unit tests are included in sniper.py for reliable functionality.

Prerequisites

Python 3.8+
Required Python packages:
requests
pandas
dontshare (for securely handling API keys; replace with your API keys if needed)


A valid Birdeye API key (stored securely, e.g., in a dontshare.py file as birdeye_api_key).
Internet connection to access the Birdeye and Solana APIs.

Installation

Clone the repository:
```
git clone https://github.com/andrei-lz/AltcoinCopySniper.git
cd crypto-trade-analyzer
```

Install dependencies:
```
pip install requests pandas
```

Set up your Birdeye API key:

Create a file named dontshare.py in the project directory.
Add your API key:
```
birdeye_api_key = "your_birdeye_api_key_here"
```


Usage
BuyerFinder.py
This script fetches trade data for a specified token and saves it to a CSV file.

Configure the script by editing the following variables in BuyerFinder.py:
```
TOKEN_ADDRESS: The Solana token address to analyze.
START_DATE and END_DATE: The date range for trade data (format: mm-dd-yyyy).
MIN_TRADE_SIZE and MAX_TRADE_SIZE: USD value range for filtering trades.
OUTPUT_FOLDER: Directory to save the output CSV file.
SORT_TYPE: Sort order for trades (asc or desc).
```

Run the script:
```
python BuyerFinder.py
```

Output:

A CSV file named <TOKEN_ADDRESS>.csv will be created in the specified OUTPUT_FOLDER with trade data.
Console output will display progress, including the number of trades processed and execution time.



sniper.py
This script analyzes early buyers of a token, their wallet ages, profitability, and interactions.

Configure the script by calling the implement_strategy function with:

token_address: The Solana token address to analyze.
api_key: Your Birdeye API key.
max_buyers: Maximum number of early buyers to analyze (default: 100).


Example usage:
```
from sniper import implement_strategy
result = implement_strategy("Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump", "your_birdeye_api_key")
print(json.dumps(result, indent=2))
```

Run unit tests:
```
python -m unittest sniper.py
```

Output:

A JSON object containing:
```
Token creation time.
List of early buyer addresses.
Analysis of new wallets among buyers.
Profit/loss (PnL) for each buyer.
Interactions between buyers.
Performance metrics (execution times for each step).
```


Configuration

API Rate Limits: Both scripts include a time.sleep(1.001) to respect Birdeye API rate limits. Adjust if necessary based on your API plan.
Output Customization: Modify the OUTPUT_FOLDER in BuyerFinder.py or add additional fields to the output in either script as needed.
Error Handling: Both scripts handle API errors with retries and stop after consecutive failures to prevent abuse.

Limitations

API Dependency: Requires a valid Birdeye API key and access to the Solana RPC endpoint.
Data Accuracy: Dependent on the accuracy and availability of Birdeye and Solana API data.
Rate Limits: Free or low-tier API plans may have restrictive limits, impacting performance for large datasets.
No File I/O in sniper.py: Unlike BuyerFinder.py, sniper.py does not save results to a file by default.
