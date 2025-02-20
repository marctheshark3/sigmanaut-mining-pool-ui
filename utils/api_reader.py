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
from .demurrage_utils import calculate_demurrage_metrics
from cachetools import TTLCache, cached
from datetime import timedelta

logger = logging.getLogger(__name__)

class ApiReader:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._session = self._create_session()
        self.wallet_address = "9fE5o7913CKKe6wvNgM11vULjTuKiopPcvCaj7t2zcJWXM2gcLu"  # TODO: Move to config
        self._initialize_caches()
        logger.info("ApiReader initialized")

    def _initialize_caches(self):
        """Initialize caches for API responses with longer TTLs"""
        # Increase cache TTLs to reduce API calls
        self._cache = {
            'ergo_tx': TTLCache(maxsize=100, ttl=1800),  # 30 minutes
            'demurrage': TTLCache(maxsize=100, ttl=1800),  # 30 minutes
            'payment_stats': TTLCache(maxsize=100, ttl=1800),  # 30 minutes
            'pool_stats': TTLCache(maxsize=100, ttl=900),  # 15 minutes
            'miner_stats': TTLCache(maxsize=100, ttl=900),  # 15 minutes
            'block_stats': TTLCache(maxsize=100, ttl=900)   # 15 minutes
        }
        logger.info("Initialized API caches with extended TTLs")

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
        """Get pool statistics with caching"""
        try:
            cached_stats = self._get_cached_data('pool_stats', 'stats')
            if cached_stats is not None:
                return cached_stats

            stats = self.data_manager.get_pool_stats()
            if stats:
                self._set_cached_data('pool_stats', 'stats', stats)
            return stats or {}
        except Exception as e:
            logger.error(f"Error getting pool stats: {str(e)}")
            return {}

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
    
    def _fetch_ergo_transactions(self) -> List[Dict[str, Any]]:
        """Fetch transactions directly from Ergo Platform API with caching"""
        try:
            # Check cache first
            if 'transactions' in self._cache['ergo_tx']:
                logger.debug("Using cached Ergo Platform API transactions")
                return self._cache['ergo_tx']['transactions']

            url = f"https://api.ergoplatform.com/api/v1/addresses/{self.wallet_address}/transactions"
            response = self._session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            transactions = data.get("items", [])
            
            # Cache the result
            self._cache['ergo_tx']['transactions'] = transactions
            logger.info("Successfully fetched and cached transactions from Ergo Platform API")
            
            return transactions
        except Exception as e:
            logger.error(f"Error fetching from Ergo Platform API: {str(e)}")
            return []

    def _get_cached_data(self, cache_key: str, data_key: str) -> Any:
        """Get data from cache with logging"""
        if cache_key in self._cache and data_key in self._cache[cache_key]:
            logger.debug(f"Cache hit for {cache_key}.{data_key}")
            return self._cache[cache_key][data_key]
        logger.debug(f"Cache miss for {cache_key}.{data_key}")
        return None

    def _set_cached_data(self, cache_key: str, data_key: str, data: Any):
        """Set data in cache with logging"""
        if cache_key in self._cache:
            self._cache[cache_key][data_key] = data
            logger.debug(f"Cached data for {cache_key}.{data_key}")

    def get_payment_stats(self) -> Dict[str, Any]:
        """Get payment statistics with improved caching"""
        try:
            # Check cache first
            cached_stats = self._get_cached_data('payment_stats', 'stats')
            if cached_stats is not None:
                return cached_stats

            # Use cached transaction data
            transactions = self._fetch_ergo_transactions()
            
            if not transactions:
                logger.warning("No transaction data available")
                default_stats = {
                    'total_paid': 0,
                    'next_demurrage': 0,
                    'last_demurrage': 0,
                    'last_payment': "Never"
                }
                self._set_cached_data('payment_stats', 'stats', default_stats)
                return default_stats
            
            # Calculate demurrage metrics
            metrics = calculate_demurrage_metrics(transactions, self.wallet_address)
            
            # Get total paid from cache if available
            pool_payments = self._get_cached_data('payment_stats', 'pool_payments')
            if pool_payments is None:
                pool_payments = self._thread_safe_request("/miningcore/payments")
                self._set_cached_data('payment_stats', 'pool_payments', pool_payments)
            
            total_paid = 0
            if pool_payments and isinstance(pool_payments, list):
                confirmed_payments = [p for p in pool_payments if p.get('status') == 'confirmed']
                total_paid = sum(float(data.get('amount', 0)) for data in confirmed_payments)
            
            result = {
                'total_paid': total_paid,
                'next_demurrage': metrics['next_demurrage'],
                'last_demurrage': metrics['last_demurrage'],
                'last_payment': metrics['last_payment']
            }
            
            # Cache the final result
            self._set_cached_data('payment_stats', 'stats', result)
            return result
            
        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            logger.exception("Full traceback:")
            return {
                'total_paid': 0,
                'next_demurrage': 0,
                'last_demurrage': 0,
                'last_payment': "Error"
            }
    
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

    def get_bonus_eligibility(self, address: str) -> Optional[Dict]:
        """Get miner's bonus eligibility status"""
        try:
            result = self._thread_safe_request(f"/sigscore/miners/{address}/bonus-eligibility")
            if result:
                return {
                    'eligible': result.get('eligible', False),
                    'qualifying_days': result.get('qualifying_days', 0),
                    'total_days_active': result.get('total_days_active', 0),
                    'needs_days': result.get('needs_days', False),
                    'analysis': result.get('analysis', '')
                }
            return None
        except Exception as e:
            logger.error(f"Error getting bonus eligibility: {str(e)}")
            return None

    # Synchronous versions of async methods
    def sync_get_miner_stats(self, address: str) -> Optional[MinerStats]:
        return self.get_miner_stats(address)

    def sync_get_miner_workers(self, address: str, days: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        return self.get_miner_workers(address, days)

    def sync_get_my_blocks(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.get_my_blocks(address, limit)

    def sync_get_miner_payment_stats(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.get_miner_payment_stats(address, limit)

    def get_demurrage_stats(self) -> List[tuple]:
        """
        Get formatted demurrage statistics for display
        
        Returns:
            List[tuple]: List of (label, value) pairs for display
        """
        try:
            stats = self.get_payment_stats()
            return [
                ('Next Demurrage:', f"{stats.get('next_demurrage', 0):.3f} ERG"),
                ('Last Demurrage:', f"{stats.get('last_demurrage', 0):.3f} ERG"),
                ('Last Payment:', stats.get('last_payment', 'Never'))
            ]
        except Exception as e:
            logger.error(f"Error getting demurrage stats: {str(e)}")
            return [
                ('Next Demurrage:', '0.000 ERG'),
                ('Last Demurrage:', '0.000 ERG'),
                ('Last Payment:', 'Error')
            ]

    def __del__(self):
        """Cleanup resources"""
        self._executor.shutdown(wait=False)
        self._session.close()

def setup_data_manager_update(app: Dash, data_manager: DataManager, interval: int = 300000):  # 5 minutes
    """Set up periodic data manager updates with rate limiting protection"""
    app.layout.children.append(dcc.Interval(id='interval-component', interval=interval))
    
    @app.callback(
        Output('interval-component', 'n_intervals'),
        Input('interval-component', 'n_intervals')
    )
    def update_data_periodically(n):
        try:
            # Only update if we haven't updated in the last 5 minutes
            data_manager.update_data()
            logger.debug("Completed periodic data update")
        except Exception as e:
            logger.error(f"Error in periodic update: {e}")
        return n