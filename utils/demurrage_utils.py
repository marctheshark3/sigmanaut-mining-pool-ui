from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Conversion factor: 1 ERG = 1e9 nanoERGs
NANOERG_FACTOR = 10**9

def calculate_demurrage_metrics(transactions: List[Dict[str, Any]], wallet_address: str) -> Dict[str, Any]:
    """
    Calculate demurrage metrics from transaction data
    
    Args:
        transactions: List of transaction data
        wallet_address: The wallet address to calculate metrics for
        
    Returns:
        Dict containing next_demurrage, last_demurrage, and last_payment
    """
    try:
        # Default return values
        default_metrics = {
            "next_demurrage": 0,
            "last_demurrage": 0,
            "last_payment": "Never"
        }
        
        if not transactions:
            logger.warning("No transactions provided for demurrage calculation")
            return default_metrics
            
        # Outgoing transactions: any transaction where at least one input's address equals our wallet
        outgoing_txs = [
            tx for tx in transactions 
            if any(inp.get("address") == wallet_address for inp in tx.get("inputs", []))
        ]
        
        if not outgoing_txs:
            logger.info(f"No outgoing transactions found for wallet address: {wallet_address}")
            return default_metrics
        
        # Most recent outgoing transaction (by timestamp in milliseconds)
        last_outgoing = max(outgoing_txs, key=lambda tx: tx.get("timestamp", 0))
        last_payment_ts = last_outgoing.get("timestamp")
        logger.info(f"Last outgoing transaction timestamp: {last_payment_ts}")
        
        # Last Demurrage: sum outputs not sent back to our wallet (convert from nanoERGs to ERGs)
        last_demurrage_nano = sum(
            out_box.get("value", 0)
            for out_box in last_outgoing.get("outputs", [])
            if out_box.get("address") != wallet_address
        )
        last_demurrage = last_demurrage_nano / NANOERG_FACTOR
        logger.info(f"Calculated last demurrage: {last_demurrage} ERG")
        
        # Next Demurrage: for transactions after the last outgoing, sum incoming outputs (to our wallet)
        next_demurrage_nano = 0
        incoming_count = 0
        for tx in transactions:
            if tx.get("timestamp", 0) > last_payment_ts:
                for out_box in tx.get("outputs", []):
                    if out_box.get("address") == wallet_address:
                        next_demurrage_nano += out_box.get("value", 0)
                        incoming_count += 1
        next_demurrage = next_demurrage_nano / NANOERG_FACTOR
        logger.info(f"Found {incoming_count} incoming transactions after last payment")
        logger.info(f"Calculated next demurrage: {next_demurrage} ERG")
        
        # Convert last payment timestamp to human-friendly string
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
        
        logger.info(f"Calculated last payment time: {last_payment_str}")
        
        return {
            "next_demurrage": next_demurrage,
            "last_demurrage": last_demurrage,
            "last_payment": last_payment_str
        }
        
    except Exception as e:
        logger.error(f"Error calculating demurrage metrics: {str(e)}")
        logger.exception("Full traceback:")
        return {
            "next_demurrage": 0,
            "last_demurrage": 0,
            "last_payment": "Error"
        } 