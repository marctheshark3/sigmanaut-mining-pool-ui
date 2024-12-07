# utils/types.py
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class MinerStats:
    address: str
    current_hashrate: float
    shares_per_second: float
    effort: float
    time_to_find: float
    last_block_found: Dict[str, Any]
    payments: Dict[str, Any]
    workers: List[Dict[str, Any]]
    balance: float = 0.0
    paid_today: float = 0.0
    total_paid: float = 0.0

class ApiException(Exception):
    """Custom exception for API-related errors"""
    pass