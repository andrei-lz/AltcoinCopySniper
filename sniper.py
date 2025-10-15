import requests
import time
import json
from typing import List, Dict, Any
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

BIRDEYE_BASE_URL = "https://public-api.birdeye.so"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

def get_token_creation_time(token_address: str, api_key: str) -> int:
    """
    Fetch the token creation time from Birdeye API.
    """
    url = f"{BIRDEYE_BASE_URL}/defi/token-overview?address={token_address}"
    headers = {
        "x-api-key": api_key,
        "x-chain": "solana"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get('data', {}).get('created_at', 0)

def get_early_trades(token_address: str, api_key: str, limit: int = 200) -> List[Dict[str, Any]]:
    """
    Fetch early trades sorted by time ascending.
    """
    url = f"{BIRDEYE_BASE_URL}/defi/txs/token?address={token_address}&tx_type=swap&offset=0&limit={limit}&sort_by=timeUnix&sort_type=asc"
    headers = {
        "x-api-key": api_key,
        "x-chain": "solana"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get('data', {}).get('items', [])

def extract_early_buyers(trades: List[Dict[str, Any]], max_buyers: int = 100) -> List[str]:
    """
    Extract unique buyer addresses from early buy trades.
    """
    buyers = set()
    for trade in trades:
        if trade.get('tradeAction') == 'buy':  # Adjusted based on possible field name
            buyer = trade.get('maker', '') or trade.get('buyer', '')
            if buyer:
                buyers.add(buyer)
            if len(buyers) >= max_buyers:
                break
    return list(buyers)

def get_wallet_creation_time(wallet_address: str) -> int:
    """
    Approximate wallet creation time by fetching the oldest transaction time via Solana RPC.
    """
    signatures = []
    before = None
    while True:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet_address, {"limit": 1000, "before": before}]
        }
        response = requests.post(SOLANA_RPC_URL, json=payload)
        if response.status_code != 200:
            return 0
        data = response.json()
        new_sigs = data.get('result', [])
        if not new_sigs:
            break
        signatures.extend(new_sigs)
        before = new_sigs[-1]['signature']
    if signatures:
        return signatures[-1].get('blockTime', 0)
    return 0

def get_wallet_pnl(wallet_addresses: List[str], api_key: str, batch_size: int = 50) -> Dict[str, float]:
    """
    Fetch realized PnL for multiple wallets using batch if possible, fallback to single.
    """
    pnls = {}
    for i in range(0, len(wallet_addresses), batch_size):
        batch = wallet_addresses[i:i+batch_size]
        for addr in batch:
            url = f"{BIRDEYE_BASE_URL}/wallet/v2/pnl?address={addr}&currency=usd"
            headers = {
                "x-api-key": api_key,
                "x-chain": "solana"
            }
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                total_pnl = sum(item.get('pnl', {}).get('realized_profit_usd', 0) for item in data.get('tokens', {}).values())
                pnls[addr] = total_pnl
            except Exception as e:
                print(f"Error fetching PnL for {addr}: {e}")
                pnls[addr] = 0.0
    return pnls

def analyze_bundle_buys(early_buyers: List[str], token_creation_time: int, new_wallet_threshold: int = 3600) -> Dict[str, Any]:
    """
    Analyze if early buyers are brand new wallets.
    """
    new_wallets = 0
    buyer_ages = {}
    for buyer in early_buyers:
        creation_time = get_wallet_creation_time(buyer)
        age_diff = creation_time - token_creation_time if creation_time > 0 else float('inf')
        buyer_ages[buyer] = age_diff
        if 0 <= age_diff <= new_wallet_threshold:
            new_wallets += 1
    percentage_new = (new_wallets / len(early_buyers)) * 100 if early_buyers else 0
    return {
        "num_new_wallets": new_wallets,
        "percentage_new": percentage_new,
        "buyer_ages": buyer_ages
    }

def get_wallet_transactions(wallet_address: str, api_key: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch recent transactions for a wallet.
    """
    url = f"{BIRDEYE_BASE_URL}/trader/txs/seek_by_time?address={wallet_address}&limit={limit}"
    headers = {
        "x-api-key": api_key,
        "x-chain": "solana"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', {}).get('items', [])
    return []

def check_wallet_interactions(early_buyers: List[str], api_key: str) -> Dict[tuple, int]:
    """
    Check interactions between early buyers by scanning transactions.
    Counts direct transfers or swaps involving pairs.
    """
    interactions = {}
    buyer_set = set(early_buyers)
    for buyer in early_buyers:
        txs = get_wallet_transactions(buyer, api_key)
        for tx in txs:
            other = tx.get('receiver', '') or tx.get('seller', '') or tx.get('buyer', '')
            if other in buyer_set and other != buyer:
                pair = tuple(sorted([buyer, other]))
                interactions[pair] = interactions.get(pair, 0) + 1
    return interactions

def implement_strategy(token_address: str, api_key: str, max_buyers: int = 100) -> Dict[str, Any]:
    """
    Implement the strategy to find and analyze early buyers.
    """
    start_time = time.time()
    
    token_creation_time = get_token_creation_time(token_address, api_key)
    token_time = time.time() - start_time
    
    trades = get_early_trades(token_address, api_key)
    trades_time = time.time() - start_time - token_time
    
    early_buyers = extract_early_buyers(trades, max_buyers)
    buyers_time = time.time() - start_time - token_time - trades_time
    
    bundle_analysis = analyze_bundle_buys(early_buyers, token_creation_time)
    bundle_time = time.time() - start_time - token_time - trades_time - buyers_time
    
    buyer_pnls = get_wallet_pnl(early_buyers, api_key)
    pnl_time = time.time() - start_time - token_time - trades_time - buyers_time - bundle_time
    
    interactions = check_wallet_interactions(early_buyers, api_key)
    inter_time = time.time() - start_time - token_time - trades_time - buyers_time - bundle_time - pnl_time
    
    good_buyers = {b: p for b, p in buyer_pnls.items() if p > 0}
    
    total_time = time.time() - start_time
    
    return {
        "token_creation_time": datetime.fromtimestamp(token_creation_time).isoformat(),
        "early_buyers": early_buyers,
        "bundle_analysis": bundle_analysis,
        "buyer_pnls": buyer_pnls,
        "good_buyers": good_buyers,
        "interactions": interactions,
        "performance": {
            "total_time_seconds": total_time,
            "token_fetch_time": token_time,
            "trades_fetch_time": trades_time,
            "buyers_extraction_time": buyers_time,
            "bundle_analysis_time": bundle_time,
            "pnl_fetch_time": pnl_time,
            "interactions_time": inter_time
        }
    }

class TestStrategy(unittest.TestCase):
    
    @patch('requests.get')
    def test_get_token_creation_time(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': {'created_at': 1690000000}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        result = get_token_creation_time("test_token", "test_key")
        self.assertEqual(result, 1690000000)
    
    @patch('requests.post')
    def test_get_wallet_creation_time(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': [{'blockTime': 1690000000}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        result = get_wallet_creation_time("test_wallet")
        self.assertEqual(result, 1690000000)
    
    @patch('requests.get')
    def test_get_early_trades(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': {'items': [{'tradeAction': 'buy', 'maker': 'addr1'}]}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        result = get_early_trades("test_token", "test_key")
        self.assertEqual(len(result), 1)
    
    def test_extract_early_buyers(self):
        trades = [{'tradeAction': 'buy', 'maker': 'addr1'}, {'tradeAction': 'sell', 'maker': 'addr2'}, {'tradeAction': 'buy', 'maker': 'addr1'}]
        result = extract_early_buyers(trades, 1)
        self.assertEqual(result, ['addr1'])
    
    @patch('requests.get')
    def test_get_wallet_pnl(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'tokens': {'tok1': {'pnl': {'realized_profit_usd': 100}}}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        result = get_wallet_pnl(["addr1"], "test_key")
        self.assertEqual(result['addr1'], 100)
    
    def test_analyze_bundle_buys(self):
        with patch('__main__.get_wallet_creation_time', return_value=1690000000):
            result = analyze_bundle_buys(["addr1"], 1689996400, 3600)
            self.assertEqual(result['num_new_wallets'], 1)

if __name__ == "__main__":
    # Example: result = implement_strategy("TOKEN_ADDRESS", "API_KEY")
    # print(json.dumps(result, indent=2))
    unittest.main()