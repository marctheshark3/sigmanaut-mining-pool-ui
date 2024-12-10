# utils/api_reader.py
from dash import Dash, dcc
from dash.dependencies import Input, Output
from .data_manager import DataManager
import logging
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import threading
from functools import wraps
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .types import MinerStats

logger = logging.getLogger(__name__)

class ApiReader:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._session = self._create_session()
        logger.info("ApiReader initialized")

    def _create_session(self):
        """Create a requests session with retry strategy"""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request with proper session handling"""
        url = f"{self.data_manager.api}{endpoint}"
        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {endpoint}: {str(e)}")
            return None

    def _thread_safe_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Execute request in a thread-safe manner"""
        try:
            return self._executor.submit(self._make_request, endpoint, params).result(timeout=30)
        except Exception as e:
            logger.error(f"Thread safe request failed: {str(e)}")
            return None

    def get_miner_stats(self, address: str) -> Optional[MinerStats]:
        """Get miner statistics"""
        try:
            result = self._thread_safe_request(f"/sigscore/miners/{address}")
            if result:
                data = {
                    'address': address,
                    'current_hashrate': result.get('current_hashrate', 0.0),
                    'shares_per_second': result.get('shares_per_second', 0.0),
                    'effort': result.get('effort', 0.0),
                    'time_to_find': result.get('time_to_find', 0.0),
                    'last_block_found': result.get('last_block_found', {}),
                    'payments': result.get('payments', {}),
                    'workers': result.get('workers', []),
                    'balance': result.get('balance', 0.0),
                    'paid_today': result.get('paid_today', 0.0),
                    'total_paid': result.get('total_paid', 0.0)
                }
                return MinerStats(**data)
            return None
        except Exception as e:
            logger.error(f"Error getting miner stats: {str(e)}")
            return None

    def get_my_blocks(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get miner blocks"""
        try:
            result = self._thread_safe_request(f"/miningcore/blocks/{address}", {"limit": limit})
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Error getting blocks: {str(e)}")
            return []
    
    def get_miner_workers(self, address: str, days: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Get miner workers data"""
        try:
            result = self._thread_safe_request(f"/sigscore/miners/{address}/workers", {"days": days})
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error getting miner workers: {str(e)}")
            return {}
    
    def get_miner_payment_stats(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get miner payment statistics"""
        try:
            return self._thread_safe_request(f"/miningcore/payments/{address}", {"limit": limit}) or []
        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            return []

    def get_pool_stats(self) -> Dict:
        return self.data_manager.get_pool_stats()

    def get_live_miner_data(self) -> Dict:
        return self.data_manager.get_live_miner_data()

    def get_total_hash_stats(self) -> Dict[str, Any]:
        """Get total hash statistics from the historical data endpoint"""
        try:
            result = self._thread_safe_request("/sigscore/history")
            # logger.info(f"Raw total hash stats response: {result}")
            
            # Ensure we have valid data
            if not result:
                logger.error("No data returned from /sigscore/history endpoint")
                return {'timestamp': [], 'total_hashrate': []}
                
            # Check if result is in expected format
            if not isinstance(result, list):
                logger.error(f"Unexpected data format from /sigscore/history. Expected list, got {type(result)}")
                return {'timestamp': [], 'total_hashrate': []}
                
            # Transform the list of records into the format needed for DataFrame
            formatted_data = {
                'timestamp': [record.get('timestamp') for record in result],
                'total_hashrate': [record.get('total_hashrate', 0) for record in result]
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error getting total hash stats: {str(e)}")
            return {'timestamp': [], 'total_hashrate': []}
    
    def get_payment_stats(self) -> float:
        """
        Get total payment statistics by summing all payment amounts
        
        Returns:
            float: Total amount of payments made, or 0 if no data available
        """
        try:
            payment_data = self._thread_safe_request("/miningcore/payments")
            if payment_data and isinstance(payment_data, list):
                total_paid = sum(float(data.get('amount', 0)) for data in payment_data)
                logger.info(f"Total payments: {total_paid}")
                return total_paid
            return 0
        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            return 0
    
    def get_block_stats(self) -> List[Dict[str, Any]]:
        """Get block statistics"""
        try:
            result = self._thread_safe_request("/miningcore/blocks")
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Error getting block stats: {str(e)}")
            return []

    def get_miner_share_stats(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get miner share statistics from miningcore"""
        try:
            result = self._thread_safe_request(f"/miningcore/minerstats/{address}", {"limit": limit})
            if not result:
                logger.warning(f"No share stats found for miner {address}")
                return []
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Error getting miner share stats: {str(e)}")
            return []

    def get_shares(self) -> List[Dict[str, Any]]:
        """
        Get current shares data for all miners
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing share information per miner
        """
        try:
            result = self._thread_safe_request("/miningcore/shares")
            if not result:
                logger.warning("No shares data available")
                return []
                
            # Ensure result is in expected format
            if not isinstance(result, list):
                logger.error(f"Unexpected shares data format: {type(result)}")
                return []
                
            # Validate data structure
            for item in result:
                if not all(k in item for k in ('miner', 'shares', 'last_share')):
                    logger.error("Share data missing required fields")
                    return []
                    
            return result
        except Exception as e:
            logger.error(f"Error getting shares data: {e}")
            return []



    # Synchronous versions of async methods
    def sync_get_miner_stats(self, address: str) -> Optional[MinerStats]:
        return self.get_miner_stats(address)

    def sync_get_miner_workers(self, address: str, days: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        return self.get_miner_workers(address, days)

    def sync_get_my_blocks(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.get_my_blocks(address, limit)

    def sync_get_miner_payment_stats(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.get_miner_payment_stats(address, limit)

    def __del__(self):
        """Cleanup resources"""
        self._executor.shutdown(wait=False)
        self._session.close()

def setup_data_manager_update(app: Dash, data_manager: DataManager, interval: int = 60000):
    app.layout.children.append(dcc.Interval(id='interval-component', interval=interval))
    
    @app.callback(
        Output('interval-component', 'n_intervals'),
        Input('interval-component', 'n_intervals')
    )
    def update_data_periodically(n):
        data_manager.update_data()
        return n