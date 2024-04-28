import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from pycoingecko import CoinGeckoAPI
from datetime import datetime
from hydra.core.global_hydra import GlobalHydra
import pytz

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
    for worker, details in data['workers'].items():
        row = {
            'worker': worker,
            'hashrate': round(details['hashrate'] / 1e6, 2), #MH/s
            'shares_per_second': round(details['sharesPerSecond'], 2),
            'created': format_datetime(data['created'])
        }
        rows.append(row)
    
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

    def __create_table_(self, table
        self.db.create_table('stats', self.stats_headers)
        self.db.create_table('block', self.block_headers)
        self.db.create_table('payment', self.payment_headers)
        self.db.create_table('live_worker', self.live_worker_headers)
        self.db.create_table('performance', self.performance_headers)
        return

    def insert_df_rows(self, df, table):
        for index, row in df.iterrows():
            self.db.insert_data(table, row.to_dict())

    def update_pool_stats(self, timenow):
        '''
        The purpose of this method is to grab all the relevant stats of the pool and network 
        '''
        stats = self.get_api_data(self.base_api)['pool']
        last_block_found = stats['lastPoolBlockTime']
        format_string = '%Y-%m-%dT%H:%M:%S.%fZ'
        date_time_obj = datetime.strptime(last_block_found, format_string)
        last_block_found = date_time_obj.strftime('%A, %B %d, %Y at %I:%M:%S %p')
        
        self.data = {'fee': stats['poolFeePercent'],
                     'paid': stats['totalPaid'],
                     'blocks': stats['totalBlocks'],
                     'last_block_found': last_block_found}

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

        self.db.insert_data('stats', self.data)

    def update_block_data(self, timenow):
        '''
        The purpose of this method is to grab the latest blocks.

        Currently we search through the last ten blocks in general

        Will need to add Rolling Effort in the df in the page itself vs db
        '''
        url = '{}/{}'.format(reader.base_api, 'blocks?pageSize=10')
        block_data = reader.get_api_data(url)
        for data in block_data:
            data['rolling_effort'] = data['effort'].expanding().mean()
            data['time_found'] = format_datetime(data.pop('created'))
            data['confirmationProgress'] = data['confirmationProgress'] * 100
            data['networkDifficulty'] = round(data['networkDifficulty'], 2)
            data['effort'] = round(data['effort'], 2)
            data['reward'] = round(data['reward'], 2)
            data['miner'] = '{}...{}'.format(data['miner'][:3], data['miner'][-5:])
            self.db.update_or_insert('block', data)


    def update_miner_data(self, timenow):
        _, erg_price = self.price_reader.get()
        miner_data = self.get_api_data('{}/{}'.format(self.base_api, 'miners?pageSize=5000'))
        miner_ls = [sample['miner'] for sample in miner_data]
        
        # time_now = pd.Timestamp.now()
        stats = self.db.fetch_data('data')
        block_data = self.db.fetch_data('block')
        networkHashrate = stats['networkhashrate'][0] # use logic to get the lastest not just the first index
        networkDifficulty = stats['networkdifficulty'][0]
        for miner in miner_ls:
            url = '{}/{}/{}'.format(self.base_api, 'miners', miner)
            mining_data = reader.get_api_data(url)        
            
            payment_data = {k: v for k, v in mining_data.items() if k not in ['performance', 'performanceSamples']}
            payment_data['Schema'] = 'PPLNS'
            payment_data['Price'] = erg_price
        
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
            
            payment_data['created_at'] = time_now
            payment_data['miner'] = miner
            miner_blocks = block_data[block_data.miner == miner]
            
            performance_df = pd.concat(worker_to_df(sample) for sample in performance_samples)
            performance_df['miner'] = miner
        
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
                live_df['miner'] = miner
                live_df['effort'] = [self.calculate_mining_effort(networkDifficulty, networkHashrate,
                                                                    temp_hash, latest) for temp_hash in live_df.hashrate]
                live_df['ttf'] = [self.calculate_time_to_find_block(networkDifficulty, networkHashrate,
                                                                      temp_hash) for temp_hash in live_df.hashrate]
                live_df['last_block_found'] = last_block_found
            
                self.insert_df_rows(live_df, 'live_worker') 
                print('live worker inserted')
                
            except KeyError:
                live_df = pd.DataFrame()
                print('no live data')
            
            self.db.insert_data('payment', payment_data)
            print('payments inserted')
        
            self.insert_df_rows(performance_df, 'performance') 
            print('performance inserted')
                
    

        
        
        
        

        
        
        

