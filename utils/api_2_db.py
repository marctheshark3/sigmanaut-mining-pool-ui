import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from pycoingecko import CoinGeckoAPI
from datetime import datetime
from hydra.core.global_hydra import GlobalHydra
import pytz
import pandas as pd

from utils.db_util import PostgreSQLDatabase

def format_datetime(time_str):
    # List of possible datetime formats to try
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # datetime with microseconds and 'Z' timezone
        "%Y-%m-%dT%H:%M:%S",      # datetime without microseconds or timezone
        "%Y-%m-%dT%H:%M:%S%z",    # datetime with timezone offset
        "%Y-%m-%dT%H:%M:%SZ"      # datetime with 'Z' but without microseconds
    ]
    
    # Attempt to parse the datetime string with each format
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")  # Converts to your desired format
        except ValueError:
            continue  # Try the next format if the current one fails
    
    # If no format matches, raise an exception
    raise ValueError(f"Time data '{time_str}' does not match any expected format")

def worker_to_df(data):
    rows = []
    total_hash = 0
    total_shares = 0
    for worker, details in data['workers'].items():
        hashrate = round(details['hashrate'] / 1e6, 2)
        shares = round(details['sharesPerSecond'], 2)
        row = {
            'worker': worker,
            'hashrate': hashrate, #MH/s
            'shares_per_second': shares,
            'created': format_datetime(data['created'])
        }
        rows.append(row)
        total_hash += hashrate
        total_shares += shares

    totals = {'worker': 'totals',
            'hashrate': total_hash, #MH/s
            'shares_per_second': total_shares,
            'created': format_datetime(data['created'])
        }
    rows.append(totals)
        
    # Create DataFrame
    return pd.DataFrame(rows)
    
class PriceReader:
    def __init__(self):
        self.cg = CoinGeckoAPI()
        
    def get(self, debug=False):
        # Fetch current price of Bitcoin (BTC) and Ergo (ERG) in USD
        if debug:
            return 10, 10
        else:
            prices = self.cg.get_price(ids=['bitcoin', 'ergo'], vs_currencies='usd')
            btc_price = prices['bitcoin']['usd']
            erg_price = prices['ergo']['usd']
            return btc_price, erg_price
            
class DataSyncer:
    def __init__(self, config_path: str):
        self.block_reward = 27 #need to calc this from emissions.csv
        self.config_path = config_path
        self.price_reader = PriceReader()
        try:
            initialize(config_path, self.config_path, version_base=None)
        except ValueError:
            GlobalHydra.instance().clear()
            initialize(config_path, self.config_path, version_base=None)
        cfg = compose(config_name='conf')

        self.api = cfg.default_values.url
        self.token_id = cfg.user_defined.token_id
        self.token_ls = cfg.default_values.token_ls
        self.base_api = cfg.default_values.base_api
        self.stats_headers = cfg.default_values.stats_cols
        self.block_headers = cfg.default_values.block_cols
        self.payment_headers = cfg.default_values.payment_headers
        self.live_worker_headers = cfg.default_values.live_worker_headers
        self.performance_headers = cfg.default_values.performance_headers
        self.miner_sample_df = DataFrame(columns=['created'])
        
        self.data = {'poolEffort': 0}

        self.db = PostgreSQLDatabase('marctheshark', 'password', 'localhost', 5432, 'mining-db')
        self.db.connect()
        self.db.get_cursor()

    def get_api_data(self, api_url):
        try:
            # Send a GET request to the API
            response = requests.get(api_url)
    
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the response as JSON (assuming the API returns JSON data)
                data = response.json()
                return data
            else:
                print(f"Failed to retrieve data: Status code {response.status_code}")
                return None
    
        except requests.exceptions.RequestException as e:
            # Handle any exceptions that occur during the request
            print(f"An error occurred: {e}")
            return None

    def __create_table__(self):
        self.db.create_table('stats', self.stats_headers)
        self.db.create_table('block', self.block_headers)
        self.db.create_table('payment', self.payment_headers)
        self.db.create_table('live_worker', self.live_worker_headers)
        self.db.create_table('performance', self.performance_headers)
        return True

    def __delete_table__(self):
        self.db.delete_data_in_batches('stats', 10)
        self.db.delete_data_in_batches('block')
        self.db.delete_data_in_batches('payment')
        self.db.delete_data_in_batches('live_worker')
        self.db.delete_data_in_batches('performance')
        return True     

    def insert_df_rows(self, df, table):
        for index, row in df.iterrows():
            self.db.insert_data(table, row.to_dict())

    def update_pool_stats(self, timenow):
        '''
        The purpose of this method is to grab all the relevant stats of the pool and network 
        '''
        stats = self.get_api_data(self.base_api)['pool']
        # last_block_found = str(format_datetime(stats['lastPoolBlockTime']))
        last_block_found = stats['lastPoolBlockTime']
        format_string = '%Y-%m-%dT%H:%M:%S.%fZ'
        date_time_obj = datetime.strptime(last_block_found, format_string)
        last_block_found = date_time_obj.strftime('%Y-%m-%d %H:%M:%S')
        
        self.data = {'fee': stats['poolFeePercent'],
                     'paid': stats['totalPaid'],
                     'blocks': stats['totalBlocks'],
                     'last_block_found': last_block_found,
                     }


        payment_data = stats['paymentProcessing'] # dict
        pool_stats = stats['poolStats'] # dict
        net_stats = stats['networkStats'] # dict

        for key in payment_data.keys():
            self.data[key] = payment_data[key]

        for key in pool_stats.keys():
            self.data[key] = pool_stats[key]

        for key in net_stats.keys():
                self.data[key] = net_stats[key]

        self.data['poolHashrate'] = round(self.data['poolHashrate'] / 1e9, 2) # GigaHash/Second
        self.data['networkHashrate'] = self.data['networkHashrate'] / 1e12 # Terra Hash/Second
        self.data['networkDifficulty'] = self.data['networkDifficulty'] / 1e15 # Peta
        self.data['insert_time_stamp'] = timenow
        self.data['poolEffort'] = round(self.calculate_mining_effort(self.data['networkDifficulty'],
                                                               self.data['networkHashrate'],
                                                               self.data['poolHashrate'] * 1e3,
                                                               last_block_found), 2)
        
        self.data['poolTTF'] = round(self.calculate_time_to_find_block(self.data['networkDifficulty'],
                                                                 self.data['networkHashrate'],
                                                                 self.data['poolHashrate'] * 1e3), 2)
        self.data['price'] = self.price_reader.get()[1]

        del self.data['payoutSchemeConfig']
        del self.data['extra']

        self.db.insert_data('stats', self.data)

    def update_block_data(self, timenow):
        '''
        The purpose of this method is to grab the latest blocks.

        Currently we search through the last ten blocks in general

        Will need to add Rolling Effort in the df in the page itself vs db
        '''
        url = '{}/{}'.format(self.base_api, 'blocks?pageSize=5000')
        block_data = self.get_api_data(url)
        for data in block_data:
            # data['rolling_effort'] = data['effort'].expanding().mean()
            data['time_found'] = format_datetime(data.pop('created'))
            data['confirmationProgress'] = data['confirmationProgress'] * 100
            data['networkDifficulty'] = round(data['networkDifficulty'], 2)
            data['effort'] = round(data['effort'], 2)
            data['reward'] = round(data['reward'], 2)
            data['miner'] = '{}...{}'.format(data['miner'][:3], data['miner'][-5:])
            self.db.update_or_insert('block', data)

    def update_miner_data(self, timenow):
        self.db.delete_data_in_batches('live_worker')
        self.db.create_table('live_worker', self.live_worker_headers)

        self.db.delete_data_in_batches('performance')
        self.db.create_table('performance', self.live_worker_headers)
        _, erg_price = self.price_reader.get()
        miner_data = self.get_api_data('{}/{}'.format(self.base_api, 'miners?pageSize=5000'))
        miner_ls = [sample['miner'] for sample in miner_data]
        
        # time_now = pd.Timestamp.now()
        stats = self.db.fetch_data('stats')
        print(stats.columns)
        stats = stats[stats.insert_time_stamp == max(stats.insert_time_stamp)]
        
        block_data = self.db.fetch_data('block')
        networkHashrate = stats['networkhashrate'].item() # use logic to get the lastest not just the first index
        networkDifficulty = stats['networkdifficulty'].item()
        for miner in miner_ls:
            url = '{}/{}/{}'.format(self.base_api, 'miners', miner)
            mining_data = self.get_api_data(url)        
            
            payment_data = {k: v for k, v in mining_data.items() if k not in ['performance', 'performanceSamples']}
            payment_data['Schema'] = 'PPLNS'
            payment_data['Price'] = erg_price
            payment_data['totalPaid'] = round(payment_data['totalPaid'], 2)
            payment_data['pendingShares'] = round(payment_data['pendingShares'], 2)
            payment_data['pendingBalance'] = round(payment_data['pendingBalance'], 2)
          
            try:
                payment_data['lastPayment'] = mining_data['lastPayment'][:-17]
                payment_data['lastPaymentLink'] = mining_data['lastPaymentLink']
                
            except KeyError: 
                payment_data['lastPayment'] = 'N/A'
                payment_data['lastPaymentLink'] = 'Keep Mining!'
        
            except TypeError:
                payment_data['lastPayment'] = 'N/A'
                payment_data['lastPaymentLink'] = 'Keep Mining!'
            
            performance_samples = mining_data.pop('performanceSamples')
            
            
            payment_data['created_at'] = timenow
            payment_data['miner'] = miner
            print(miner, block_data.miner)
            shorten_miner = '{}...{}'.format(miner[:3], miner[-5:])

            miner_blocks = block_data[block_data.miner == shorten_miner]
            try: 
                performance_df = pd.concat(worker_to_df(sample) for sample in performance_samples)
                performance_df['miner'] = miner

            except ValueError:
                # might need to add something here
                pass
        
            if miner_blocks.empty:
                # still need to adjust to pull from performance table for this miner
                latest = min(performance_df.created) 
                last_block_found = 'N/A'
        
            else:
                latest = str(max(miner_blocks.time_found))
                last_block_found = latest
        
            try:
                live_performance = mining_data.pop('performance')
                live_df = worker_to_df(live_performance)
                live_df['hashrate'] = round(live_df['hashrate'], 0)
                live_df['miner'] = miner
                if last_block_found == 'N/A':
                    live_df['effort'] = 0
                else:
                    live_df['effort'] = [round(self.calculate_mining_effort(networkDifficulty, networkHashrate,
                                                                    temp_hash, latest), 2) for temp_hash in live_df.hashrate]
                live_df['ttf'] = [round(self.calculate_time_to_find_block(networkDifficulty, networkHashrate,
                                                                      temp_hash), 2) for temp_hash in live_df.hashrate]
                live_df['last_block_found'] = last_block_found
            
                self.insert_df_rows(live_df, 'live_worker') 
                
            except KeyError:
                live_df = pd.DataFrame()
                print('no live data for miner {}'.format(miner))

            
            
            self.db.insert_data('payment', payment_data)
        
            self.insert_df_rows(performance_df, 'performance') 
        return

    def calculate_mining_effort(self, network_difficulty, network_hashrate, hashrate, last_block_timestamp):
        """
        Calculate the mining effort for the pool to find a block on Ergo blockchain based on the given timestamp.
        
        :param network_difficulty: The current difficulty of the Ergo network.
        :param network_hashrate: The total hash rate of the Ergo network (in hashes per second).
        :param pool_hashrate: The hash rate of the mining pool (in hashes per second).
        :param last_block_timestamp: Timestamp of the last block found in ISO 8601 format.
        :return: The estimated mining effort for the pool.
        """

        network_difficulty = network_difficulty * 1e15
        network_hashratev = network_hashrate * 1e12
        hashrate = hashrate * 1e6
        
        # Parse the last block timestamp
        time_format = '%Y-%m-%d %H:%M:%S' 
        last_block_time = datetime.strptime(last_block_timestamp, time_format)
        last_block_time = last_block_time.replace(tzinfo=pytz.utc)  # Assume the timestamp is in UTC
        
        # Get the current time in UTC
        now = datetime.now(pytz.utc)
        
        # Calculate the time difference in seconds
        time_since_last_block = (now - last_block_time).total_seconds()
        
        # Hashes to find a block at current difficulty
        hashes_to_find_block = network_difficulty# This is a simplification
        
        # Total hashes by the network in the time since last block
        total_network_hashes = network_hashrate * time_since_last_block
        
        # Pool's share of the total network hashes
        pool_share_of_hashes = (hashrate / network_hashrate ) * total_network_hashes
        
        # Effort is the pool's share of hashes divided by the number of hashes to find a block
        effort = pool_share_of_hashes / hashes_to_find_block * 100
        
        return round(effort, 3)

    def calculate_time_to_find_block(self, network_difficulty, network_hashrate, hashrate):
        """
        Calculate the time to find a block on Ergo blockchain based on the given timestamp.
        
        :param network_difficulty: The current difficulty of the Ergo network.
        :param network_hashrate: The total hash rate of the Ergo network (in hashes per second).
        :param pool_hashrate: The hash rate of the mining pool (in hashes per second).
        :param last_block_timestamp: Timestamp of the last block found in ISO 8601 format.
        :return: The estimated time to find a block for the pool.
        """
    
        network_difficulty = network_difficulty * 1e15
        network_hashrate = network_hashrate * 1e12
        hashrate = hashrate * 1e6
        
        # Hashes to find a block at current difficulty
        hashes_to_find_block = network_difficulty  # This is a simplification
        
        # Calculate the time to find a block
        try:
            time_to_find_block = hashes_to_find_block / hashrate
        except ZeroDivisionError:
            time_to_find_block = 1
        
        return round(time_to_find_block / 3600 / 24, 3)
    

        
        
        
        

        
        
        

