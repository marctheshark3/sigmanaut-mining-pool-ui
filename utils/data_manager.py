# data_manager.py
from typing import Dict, Any
import logging
import asyncio
import aiohttp
from cachetools import TTLCache
from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra
import redis
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, config_path: str):
        try:
            # Convert absolute path to relative path if needed
            if os.path.isabs(config_path):
                config_path = os.path.relpath(config_path, os.getcwd())
            
            # Ensure the config path is relative to the current directory
            config_path = config_path.replace('\\', '/')
            if config_path.startswith('/'):
                config_path = config_path[1:]
            
            logger.debug(f"Using config path: {config_path}")
            
            try:
                initialize(version_base=None, config_path=config_path)
            except ValueError:
                GlobalHydra.instance().clear()
                initialize(version_base=None, config_path=config_path)
            
            cfg = compose(config_name="config")
            self.api = cfg.default_values.api
            self.data = {}
            self._initialize_caches()
            self._initialize_redis()
        except Exception as e:
            logger.error(f"Failed to initialize DataManager: {e}", exc_info=True)
            raise

    def _initialize_redis(self):
        """Initialize Redis connection if available"""
        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self.redis = redis.from_url(redis_url)
                logger.info("Successfully connected to Redis")
            else:
                self.redis = None
                logger.info("No Redis URL provided, using in-memory cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None

    def _initialize_caches(self):
        """Initialize caches with longer TTLs and proper maxsize"""
        self.caches = {
            'total_hash_stats': TTLCache(maxsize=100, ttl=1800),  # 30 minutes
            'payment_stats': TTLCache(maxsize=100, ttl=1800),     # 30 minutes
            'pool_stats': TTLCache(maxsize=100, ttl=1800),        # 30 minutes
            'block_stats': TTLCache(maxsize=100, ttl=1800),       # 30 minutes
            'live_miner_data': TTLCache(maxsize=1000, ttl=1800),  # 30 minutes
            'shares': TTLCache(maxsize=100, ttl=300)              # 5 minutes
        }
        logger.info("Initialized DataManager caches with extended TTLs")

    def _get_cached_data(self, cache_key: str) -> Any:
        """Get data from cache with Redis fallback"""
        # Try Redis first if available
        if self.redis:
            try:
                data = self.redis.get(cache_key)
                if data:
                    logger.debug(f"Redis cache hit for {cache_key}")
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis error for {cache_key}: {e}")

        # Fallback to in-memory cache
        if cache_key in self.caches and cache_key in self.caches[cache_key]:
            logger.debug(f"Memory cache hit for {cache_key}")
            return self.caches[cache_key][cache_key]
        
        logger.debug(f"Cache miss for {cache_key}")
        return None

    def _set_cached_data(self, cache_key: str, data: Any):
        """Set data in cache with Redis support"""
        # Try to store in Redis if available
        if self.redis:
            try:
                self.redis.setex(
                    cache_key,
                    self.caches[cache_key].ttl if cache_key in self.caches else 1800,
                    json.dumps(data)
                )
                logger.debug(f"Stored data in Redis for {cache_key}")
            except Exception as e:
                logger.error(f"Redis storage error for {cache_key}: {e}")

        # Always store in memory cache as fallback
        if cache_key in self.caches:
            self.caches[cache_key][cache_key] = data
            logger.debug(f"Stored data in memory cache for {cache_key}")

    async def _make_request(self, url: str) -> Dict:
        """Make async HTTP request with error handling and retries"""
        retries = 3
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        logger.error(f"API request failed: {response.status}")
                        if attempt < retries - 1:  # don't sleep on the last attempt
                            await asyncio.sleep(1 * (attempt + 1))  # exponential backoff
            except Exception as e:
                logger.error(f"Request error for {url}: {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
        return None

    def _get_endpoint_data(self, endpoint: str) -> Dict:
        """Get endpoint data with improved caching and error handling"""
        cache_key = endpoint.strip('/').replace('/', '_')
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        # If not in cache, make the request
        url = f'{self.api}{endpoint}'
        try:
            result = asyncio.run(self._make_request(url))
            if result is not None:
                self._set_cached_data(cache_key, result)
                return result
            
            # If request failed, return last known data from cache if available
            if cache_key in self.caches:
                logger.warning(f"Using stale cache data for {cache_key} due to failed request")
                return self.caches[cache_key].get(cache_key, {})
            
            return {}
        except Exception as e:
            logger.error(f"Error fetching endpoint {endpoint}: {e}")
            return {}

    def get_total_hash_stats(self) -> Dict:
        """Get total hash statistics with caching"""
        cached_data = self._get_cached_data('total_hash_stats')
        if cached_data is not None:
            return cached_data
        
        data = self._get_endpoint_data('/sigscore/history')
        if data:
            self._set_cached_data('total_hash_stats', data)
        return data or {}

    def get_payment_stats(self) -> Dict[str, Any]:
        """Get payment statistics with caching"""
        cached_data = self._get_cached_data('payment_stats')
        if cached_data is not None:
            return cached_data
            
        data = self._get_endpoint_data('/miningcore/payments')
        if not data:
            return {'total_paid': 0}
            
        # Filter for confirmed transactions only
        confirmed_payments = [p for p in data if p.get('status') == 'confirmed']
        result = {'total_paid': sum(p['amount'] for p in confirmed_payments)}
        
        self._set_cached_data('payment_stats', result)
        return result

    def get_pool_stats(self) -> Dict:
        """Get pool statistics with caching"""
        cached_data = self._get_cached_data('pool_stats')
        if cached_data is not None:
            return cached_data
            
        data = self._get_endpoint_data('/miningcore/poolstats')
        if data:
            self._set_cached_data('pool_stats', data)
        return data or {}

    def get_shares(self) -> Dict:
        """Get shares data with shorter cache duration"""
        cached_data = self._get_cached_data('shares')
        if cached_data is not None:
            return cached_data
            
        data = self._get_endpoint_data('/miningcore/shares')
        if data:
            self._set_cached_data('shares', data)
        return data or {}

    def get_block_stats(self) -> Dict:
        """Get block statistics with caching"""
        cached_data = self._get_cached_data('block_stats')
        if cached_data is not None:
            return cached_data
            
        data = self._get_endpoint_data('/miningcore/blocks')
        if data:
            self._set_cached_data('block_stats', data)
        return data or {}

    def get_live_miner_data(self) -> Dict:
        """Get live miner data with caching"""
        cached_data = self._get_cached_data('live_miner_data')
        if cached_data is not None:
            return cached_data
            
        data = self._get_endpoint_data('/sigscore/miners')
        if data:
            self._set_cached_data('live_miner_data', data)
        return data or {}

    def update_data(self):
        """Update all cached data in a controlled manner"""
        try:
            # Update each cache only if it's expired
            for cache_key in self.caches:
                if cache_key not in self.caches[cache_key]:
                    if cache_key == 'total_hash_stats':
                        self.get_total_hash_stats()
                    elif cache_key == 'payment_stats':
                        self.get_payment_stats()
                    elif cache_key == 'pool_stats':
                        self.get_pool_stats()
                    elif cache_key == 'block_stats':
                        self.get_block_stats()
                    elif cache_key == 'live_miner_data':
                        self.get_live_miner_data()
                    elif cache_key == 'shares':
                        self.get_shares()
        except Exception as e:
            logger.error(f"Error updating data: {e}")
