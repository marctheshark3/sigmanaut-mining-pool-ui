import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from hydra.core.global_hydra import GlobalHydra
import threading
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        self.data: Dict[str, Any] = {}
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def update_data(self):
        logger.info("Starting data update")
        try:
            with self._lock:
                self.data['total_hash_stats'] = self.get_total_hash_stats()
                self.data['payment_stats'] = self.get_payment_stats()
                self.data['pool_stats'] = self.get_pool_stats()
                self.data['shares'] = self.get_shares()
                self.data['block_stats'] = self.get_block_stats()
                self.data['live_miner_data'] = self.get_live_miner_data()
            logger.info("Data update completed successfully")
        except Exception as e:
            logger.error(f"Error during data update: {e}", exc_info=True)

    def start_update_loop(self, update_interval: float):
        def update_loop():
            while not self._stop_event.is_set():
                self.update_data()
                self._stop_event.wait(update_interval)

        threading.Thread(target=update_loop, daemon=True).start()
        logger.info(f"Update loop started with interval: {update_interval} seconds")

    def stop_update_loop(self):
        self._stop_event.set()
        logger.info("Update loop stop signal sent")

    def get_api_data(self, api_url: str):
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {api_url}: {e}")
            return None

    def get_total_hash_stats(self):
        url = f'{self.api}/sigscore/history'
        return self.get_api_data(url)

    def get_payment_stats(self):
        url = f'{self.api}/miningcore/payments'
        payment_data = self.get_api_data(url)
        paid = sum(data['amount'] for data in payment_data) if payment_data else 0
        return paid

    def get_pool_stats(self):
        url = f'{self.api}/miningcore/poolstats'
        pool_data = self.get_api_data(url)
        return pool_data[-1] if pool_data else None

    def get_shares(self):
        url = f'{self.api}/miningcore/shares'
        return self.get_api_data(url)

    def get_block_stats(self):
        url = f'{self.api}/miningcore/blocks'
        return self.get_api_data(url)

    def get_live_miner_data(self):
        url = f'{self.api}/sigscore/miners'
        return self.get_api_data(url)

class ApiReader:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def get_total_hash_stats(self):
        with self.data_manager._lock:
            return self.data_manager.data.get('total_hash_stats')

    def get_payment_stats(self):
        with self.data_manager._lock:
            return self.data_manager.data.get('payment_stats')

    def get_pool_stats(self):
        with self.data_manager._lock:
            return self.data_manager.data.get('pool_stats')

    def get_shares(self):
        with self.data_manager._lock:
            return self.data_manager.data.get('shares')

    def get_block_stats(self):
        with self.data_manager._lock:
            return self.data_manager.data.get('block_stats')

    def get_my_blocks(self, address: str):
        url = f'{self.data_manager.api}/miningcore/blocks/{address}'
        return self.data_manager.get_api_data(url)

    def get_miner_stats(self, address: str):
        url = f'{self.data_manager.api}/sigscore/miners/{address}'
        return self.data_manager.get_api_data(url)

    def get_miner_payment_stats(self, address: str):
        url = f'{self.data_manager.api}/miningcore/payments/{address}'
        return self.data_manager.get_api_data(url)

    def get_live_miner_data(self):
        with self.data_manager._lock:
            return self.data_manager.data.get('live_miner_data')

    def get_miner_workers(self, address: str):
        url = f'{self.data_manager.api}/sigscore/miners/{address}/workers'
        return self.data_manager.get_api_data(url)

    def get_top_miners(self, limit: int = 20):
        url = f'{self.data_manager.api}/sigscore/miners/top?limit={limit}'
        return self.data_manager.get_api_data(url)

    def get_all_miners(self, limit: int = 100, offset: int = 0):
        url = f'{self.data_manager.api}/sigscore/miners?limit={limit}&offset={offset}'
        return self.data_manager.get_api_data(url)
