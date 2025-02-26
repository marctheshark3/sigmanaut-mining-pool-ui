import requests
import json
from datetime import datetime

# Conversion factor: 1 ERG = 1e9 nanoERGs
NANOERG_FACTOR = 10**9

def fetch_transactions(wallet_address):
    url = f"https://api.ergoplatform.com/api/v1/addresses/{wallet_address}/transactions"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error fetching transactions: {response.status_code}")
    return response.json()

def calculate_demurrage_metrics(data, wallet_address):
    """
    Given transaction data and a wallet address, compute:
      - next_demurrage: sum of incoming ERGs (converted from nanoERGs) after the last payout.
      - last_demurrage: sum of ERGs sent out in the most recent outgoing payment.
      - last_payment: a human-friendly string (e.g., "2 days ago") for the time elapsed since the last outgoing payment.
    
    This code assumes that any transaction with an input from your wallet is an outgoing payment.
    Change outputs (those that go back to your wallet) are not included in the last demurrage amount.
    """
    transactions = data.get("items", [])
    
    # Outgoing transactions: any transaction where at least one input's address equals our wallet.
    outgoing_txs = [
        tx for tx in transactions 
        if any(inp.get("address") == wallet_address for inp in tx.get("inputs", []))
    ]
    
    if not outgoing_txs:
        raise ValueError("No outgoing transactions found for wallet address.")
    
    # Most recent outgoing transaction (by timestamp in milliseconds)
    last_outgoing = max(outgoing_txs, key=lambda tx: tx.get("timestamp", 0))
    last_payment_ts = last_outgoing.get("timestamp")
    
    # Last Demurrage: sum outputs not sent back to our wallet (convert from nanoERGs to ERGs)
    last_demurrage_nano = sum(
        out_box.get("value", 0)
        for out_box in last_outgoing.get("outputs", [])
        if out_box.get("address") != wallet_address
    )
    last_demurrage = last_demurrage_nano / NANOERG_FACTOR
    
    # Next Demurrage: for transactions after the last outgoing, sum incoming outputs (to our wallet).
    next_demurrage_nano = 0
    for tx in transactions:
        if tx.get("timestamp", 0) > last_payment_ts:
            for out_box in tx.get("outputs", []):
                if out_box.get("address") == wallet_address:
                    next_demurrage_nano += out_box.get("value", 0)
    next_demurrage = next_demurrage_nano / NANOERG_FACTOR
    
    # Convert last payment timestamp to human-friendly string.
    last_payment_dt = datetime.fromtimestamp(last_payment_ts / 1000.0)
    now = datetime.now()
    delta = now - last_payment_dt
    if delta.days > 0:
        last_payment_str = f"{delta.days} days ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        last_payment_str = f"{hours} hours ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        last_payment_str = f"{minutes} minutes ago"
    else:
        last_payment_str = "Just now"
    
    return {
        "next_demurrage": next_demurrage,
        "last_demurrage": last_demurrage,
        "last_payment": last_payment_str
    }

if __name__ == "__main__":
    wallet_address = "9fE5o7913CKKe6wvNgM11vULjTuKiopPcvCaj7t2zcJWXM2gcLu"
    data = fetch_transactions(wallet_address)
    metrics = calculate_demurrage_metrics(data, wallet_address)
    print("Next Demurrage (ERGs):", metrics["next_demurrage"])
    print("Last Demurrage (ERGs):", metrics["last_demurrage"])
    print("Last Payment:", metrics["last_payment"])
