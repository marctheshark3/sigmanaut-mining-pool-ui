# data_manager.py
from typing import Dict
import logging
import asyncio
import aiohttp
from cachetools import TTLCache
from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, config_path: str):
        try:
            initialize(config_path, config_path, version_base=None)
        except ValueError:
            GlobalHydra.instance().clear()
            initialize(config_path, config_path, version_base=None)
        
        cfg = compose(config_name='conf')
        self.api = cfg.default_values.api
        self.data = {}
        self._initialize_caches()

    def _initialize_caches(self):
        self.caches = {
            'total_hash_stats': TTLCache(maxsize=100, ttl=300),
            'payment_stats': TTLCache(maxsize=100, ttl=300),
            'pool_stats': TTLCache(maxsize=100, ttl=60),
            'block_stats': TTLCache(maxsize=100, ttl=60),
            'live_miner_data': TTLCache(maxsize=1000, ttl=60),
            'shares': TTLCache(maxsize=100, ttl=30)
        }

    async def _make_request(self, url: str) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json() if response.status == 200 else None
        except Exception as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None

    def _get_endpoint_data(self, endpoint: str) -> Dict:
        url = f'{self.api}{endpoint}'
        return asyncio.run(self._make_request(url))

    def get_total_hash_stats(self) -> Dict:
        return self._get_endpoint_data('/sigscore/history')

    def get_payment_stats(self) -> float:
        data = self._get_endpoint_data('/miningcore/payments')
        return sum(d['amount'] for d in data) if data else 0

    def get_pool_stats(self) -> Dict:
        return self._get_endpoint_data('/miningcore/poolstats') or {}

    def get_shares(self) -> Dict:
        return self._get_endpoint_data('/miningcore/shares') or {}

    def get_block_stats(self) -> Dict:
        return self._get_endpoint_data('/miningcore/blocks') or {}

    def get_live_miner_data(self) -> Dict:
        return self._get_endpoint_data('/sigscore/miners') or {}

    def update_data(self):
        try:
            self.data.update({
                'total_hash_stats': self.get_total_hash_stats(),
                'payment_stats': self.get_payment_stats(),
                'pool_stats': self.get_pool_stats(),
                'block_stats': self.get_block_stats(),
                'live_miner_data': self.get_live_miner_data(),
                'shares': self.get_shares()
            })
        except Exception as e:
            logger.error(f"Error updating data: {e}")
