import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from hydra.core.global_hydra import GlobalHydra

class ApiReader:
    def __init__(self, config_path: str):
        try:
            initialize(config_path, config_path, version_base=None)
        except ValueError:
            GlobalHydra.instance().clear()
            initialize(config_path, config_path, version_base=None)
        cfg = compose(config_name='conf')
        self.api = cfg.default_values.api

    def get_api_data(self, api_url):
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to retrieve data: Status code {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
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

    def get_my_blocks(self, address):
        url = f'{self.api}/miningcore/blocks/{address}'
        return self.get_api_data(url)

    def get_miner_stats(self, address):
        url = f'{self.api}/sigscore/miners/{address}'
        return self.get_api_data(url)

    def get_miner_payment_stats(self, address):
        url = f'{self.api}/miningcore/payments/{address}'
        return self.get_api_data(url)

    def get_live_miner_data(self):
        url = f'{self.api}/sigscore/miners'
        return self.get_api_data(url)

    def get_miner_workers(self, address):
        url = f'{self.api}/sigscore/miners/{address}/workers'
        return self.get_api_data(url)

    # def get_miner_samples(self, address):
    #     url = f'{self.api}/sigscore/miners/{address}/samples'
    #     return self.get_api_data(url)

    def get_top_miners(self, limit=20):
        url = f'{self.api}/sigscore/miners/top?limit={limit}'
        return self.get_api_data(url)

    def get_all_miners(self, limit=100, offset=0):
        url = f'{self.api}/sigscore/miners?limit={limit}&offset={offset}'
        return self.get_api_data(url)