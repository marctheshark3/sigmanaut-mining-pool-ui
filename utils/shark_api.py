import requests
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from cachetools import TTLCache, cached
from functools import wraps
import asyncio
import aiohttp
from dataclasses import dataclass
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from hydra.core.global_hydra import GlobalHydra
import threading
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, config_path: str):
        """Initialize DataManager with configuration"""
        logger.info(f"Initializing DataManager with config path: {config_path}")
        try:
            initialize(config_path, config_path, version_base=None)
        except ValueError:
            logger.warning("GlobalHydra instance already initialized. Clearing and reinitializing.")
            GlobalHydra.instance().clear()
            initialize(config_path, config_path, version_base=None)
        
        cfg = compose(config_name='conf')
        self.api = cfg.default_values.api
        self.data = {}
        self._initialize_caches()
        logger.info("DataManager initialized successfully")

    def _initialize_caches(self):
        """Initialize data caches with TTL"""
        self.caches = {
            'total_hash_stats': TTLCache(maxsize=100, ttl=300),
            'payment_stats': TTLCache(maxsize=100, ttl=300),
            'pool_stats': TTLCache(maxsize=100, ttl=60),
            'block_stats': TTLCache(maxsize=100, ttl=60),
            'live_miner_data': TTLCache(maxsize=1000, ttl=60),
            'shares': TTLCache(maxsize=100, ttl=30)
        }

    def update_data(self):
        """Update all cached data"""
        logger.info("--------- UPDATING CORE DATA ---------")
        
        self.data['total_hash_stats'] = self.get_total_hash_stats()
        logger.info("(1/6) Gathered Total Hash Stats")
        
        self.data['payment_stats'] = self.get_payment_stats()
        logger.info("(2/6) Gathered Payments Stats")
        
        self.data['pool_stats'] = self.get_pool_stats()
        logger.info("(3/6) Gathered Pool Stats")
        
        self.data['block_stats'] = self.get_block_stats()
        logger.info("(4/6) Gathered Block Stats")
        
        self.data['live_miner_data'] = self.get_live_miner_data()
        logger.info("(5/6) Gathered Live Miner Stats")

        self.data['shares'] = self.get_shares()
        logger.info("(6/6) Gathered Shares Data")
        
        logger.info("--------- UPDATING COMPLETE --------- \n")

    async def _make_request(self, url: str) -> Dict:
        """Make async HTTP request with error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None

    def get_total_hash_stats(self) -> Dict:
        """Get total hash statistics"""
        url = f'{self.api}/sigscore/history'
        return asyncio.run(self._make_request(url))

    def get_payment_stats(self) -> float:
        """Get payment statistics"""
        url = f'{self.api}/miningcore/payments'
        payment_data = asyncio.run(self._make_request(url))
        if payment_data:
            paid = sum(data['amount'] for data in payment_data)
            logger.info(f"Total payments: {paid}")
            return paid
        return 0

    def get_pool_stats(self) -> Dict:
        """Get pool statistics"""
        url = f'{self.api}/miningcore/poolstats'
        pool_data = asyncio.run(self._make_request(url))
        return pool_data

    def get_shares(self) -> Dict:
        """Get current shares data"""
        url = f'{self.api}/miningcore/shares'
        return asyncio.run(self._make_request(url))

    def get_block_stats(self) -> Dict:
        """Get block statistics"""
        url = f'{self.api}/miningcore/blocks'
        return asyncio.run(self._make_request(url))

    def get_live_miner_data(self) -> Dict:
        """Get live miner data"""
        url = f'{self.api}/sigscore/miners'
        return asyncio.run(self._make_request(url))

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

class ApiException(Exception):
    """Custom exception for API-related errors"""
    pass

class ApiReader:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._session = None
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        logger.info("ApiReader initialized")

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        url = f"{self.data_manager.api}{endpoint}"
        try:
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                error_text = await response.text()
                raise ApiException(f"API request failed: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Request error for {endpoint}: {str(e)}")
            raise ApiException(f"Request failed: {str(e)}")

    def _run_async(self, coro):
        try:
            return self._loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Error in _run_async: {str(e)}")
            raise

    def get_total_hash_stats(self) -> Dict:
        return self.data_manager.data.get('total_hash_stats', {})

    def get_payment_stats(self) -> float:
        return self.data_manager.data.get('payment_stats', 0)

    def get_pool_stats(self) -> Dict:
        return self.data_manager.data.get('pool_stats', {})

    def get_shares(self) -> Dict:
        return self.data_manager.data.get('shares', {})

    def get_block_stats(self) -> Dict:
        return self.data_manager.data.get('block_stats', {})

    def get_live_miner_data(self) -> Dict:
        return self.data_manager.data.get('live_miner_data', {})

    async def get_miner_stats(self, address: str) -> MinerStats:
        try:
            data = await self._make_request(f"/sigscore/miners/{address}")
            return MinerStats(**data)
        except Exception as e:
            logger.error(f"Error fetching miner stats for {address}: {e}")
            raise ApiException(f"Failed to get miner stats: {str(e)}")

    async def get_miner_workers(self, address: str, days: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        return await self._make_request(f"/sigscore/miners/{address}/workers", {"days": days})

    async def get_my_blocks(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return await self._make_request(f"/miningcore/blocks/{address}", {"limit": limit})

    async def get_miner_payment_stats(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return await self._make_request(f"/miningcore/payments/{address}", {"limit": limit})

    def sync_get_miner_stats(self, address: str) -> MinerStats:
        return self._run_async(self.get_miner_stats(address))

    def sync_get_miner_workers(self, address: str, days: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        return self._run_async(self.get_miner_workers(address, days))

    def sync_get_my_blocks(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._run_async(self.get_my_blocks(address, limit))

    def sync_get_miner_payment_stats(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._run_async(self.get_miner_payment_stats(address, limit))

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
        if self._loop and not self._loop.is_closed():
            self._loop.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __del__(self):
        if hasattr(self, '_loop') and self._loop and not self._loop.is_closed():
            self._loop.run_until_complete(self.close())

def setup_data_manager_update(app: Dash, data_manager: DataManager, interval: int = 60000):
    """Set up periodic data updates for Dash app"""
    app.layout.children.append(dcc.Interval(id='interval-component', interval=interval, n_intervals=0))

    @app.callback(
        Output('interval-component', 'n_intervals'),
        Input('interval-component', 'n_intervals')
    )
    def update_data_periodically(n):
        data_manager.update_data()
        return n