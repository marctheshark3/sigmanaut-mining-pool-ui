import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from hydra.core.global_hydra import GlobalHydra
import threading
import logging
import time
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
def setup_data_manager_update(app, data_manager, interval=2*60000):  # interval in milliseconds
    app.layout.children.append(dcc.Interval(id='interval-component', interval=interval, n_intervals=0))

    @app.callback(Output('interval-component', 'n_intervals'),
                  Input('interval-component', 'n_intervals'))
    def update_data_periodically(n):
        data_manager.update_data()
        return n
        
class DataManager:
    def __init__(self, config_path: str):
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
        logger.info("DataManager initialized successfully")

    def update_data(self):
        logger.info("--------- UPDATING CORE DATA ---------")
        
        self.data['total_hash_stats'] = self.get_total_hash_stats()
        logger.info("(1/5) Gathered Total Hash Stats")
        
        self.data['payment_stats'] = self.get_payment_stats()
        logger.info("(2/5) Gathered Payments Stats")
        
        self.data['pool_stats'] = self.get_pool_stats()
        logger.info("(3/5) Gathered Pool Stats")
        
        self.data['block_stats'] = self.get_block_stats()
        logger.info("(4/5) Gathered Block Stats")
        
        self.data['live_miner_data'] = self.get_live_miner_data()
        logger.info("(5/5) Gathered Live Miner Stats")
        
        logger.info("--------- UPDATING  COMPLETE --------- \n")

    def get_api_data(self, api_url):
        logger.debug(f"Fetching data from API: {api_url}")
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                logger.debug(f"Successfully retrieved data from {api_url}")
                return response.json()
            else:
                logger.error(f"Failed to retrieve data from {api_url}: Status code {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while fetching data from {api_url}: {e}")
            return None

    def get_total_hash_stats(self):
        url = f'{self.api}/sigscore/history'
        return self.get_api_data(url)

    def get_payment_stats(self):
        url = f'{self.api}/miningcore/payments'
        payment_data = self.get_api_data(url)
        paid = 0
        for data in payment_data:
            paid += data['amount']
        logger.info(f"Total payments: {paid}")
        return paid

    def get_pool_stats(self):
        url = f'{self.api}/miningcore/poolstats'
        pool_data = self.get_api_data(url)
        return pool_data[-1] if pool_data else None

    def get_shares(self):
        url = f'{self.api}/miningcore/shares'
        return self.get_api_data(url)

    def get_mining_stats(self):
        url = f'{self.api}/miningcore/minerstats'
        return self.get_api_data(url)

    def get_block_stats(self):
        url = f'{self.api}/miningcore/blocks'
        return self.get_api_data(url)

    def get_live_miner_data(self):
        url = f'{self.api}/sigscore/miners'
        return self.get_api_data(url)

class ApiReader:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        logger.info("ApiReader initialized")

    def get_total_hash_stats(self):
        logger.debug("Retrieving total hash stats")
        return self.data_manager.data['total_hash_stats']

    def get_payment_stats(self):
        logger.debug("Retrieving payment stats")
        return self.data_manager.data['payment_stats']

    def get_pool_stats(self):
        logger.debug("Retrieving pool stats")
        return self.data_manager.data['pool_stats']

    def get_shares(self):
        logger.debug("Retrieving shares")
        return self.data_manager.data['shares']

    def get_mining_stats(self):
        logger.debug("Retrieving mining stats")
        return self.data_manager.data['mining_stats']

    def get_block_stats(self):
        logger.debug("Retrieving block stats")
        return self.data_manager.data['block_stats']

    def get_my_blocks(self, address):
        logger.info(f"Retrieving blocks for address: {address}")
        url = f'{self.data_manager.api}/miningcore/blocks/{address}'
        return self.data_manager.get_api_data(url)

    def get_miner_stats(self, address):
        logger.info(f"Retrieving miner stats for address: {address}")
        url = f'{self.data_manager.api}/sigscore/miners/{address}'
        return self.data_manager.get_api_data(url)

    def get_miner_payment_stats(self, address):
        logger.info(f"Retrieving miner payment stats for address: {address}")
        url = f'{self.data_manager.api}/miningcore/payments/{address}'
        return self.data_manager.get_api_data(url)

    def get_live_miner_data(self):
        logger.debug("Retrieving live miner data")
        return self.data_manager.data['live_miner_data']

    def get_miner_workers(self, address):
        logger.info(f"Retrieving miner workers for address: {address}")
        url = f'{self.data_manager.api}/sigscore/miners/{address}/workers'
        return self.data_manager.get_api_data(url)

    def get_top_miners(self, limit=20):
        logger.info(f"Retrieving top {limit} miners")
        url = f'{self.data_manager.api}/sigscore/miners/top?limit={limit}'
        return self.data_manager.get_api_data(url)

    def get_all_miners(self, limit=100, offset=0):
        logger.info(f"Retrieving all miners with limit {limit} and offset {offset}")
        url = f'{self.data_manager.api}/sigscore/miners?limit={limit}&offset={offset}'
        return self.data_manager.get_api_data(url)

    def get_miner_swap_payments(self, address):
        logger.info(f"Retrieving miner swap payments for address: {address}")
        url = f'{self.data_manager.api}/miningcore/swap_payments/{address}'
        return self.data_manager.get_api_data(url)