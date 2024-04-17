import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from pycoingecko import CoinGeckoAPI
from datetime import datetime
from hydra.core.global_hydra import GlobalHydra
import pytz

debug=False

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

class SigmaWalletReader:
    # def __init__(self, api, token_id, token_ls_url='https://api.ergo.aap.cornell.edu/api/v1/tokens/'):
    #     self.api = api
    #     self.token_id = token_id
    #     self.token_ls = token_ls_url

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
        self.miner_sample_df = DataFrame(columns=['created'])
        self.btc_price, self.erg_price = self.price_reader.get(debug)
        self.data = {'poolEffort': 0}

    def update_data(self):
        miner_data = self.get_api_data('{}/{}'.format(self.base_api, 'miners'))
        miner_ls = [sample['miner'] for sample in miner_data]

        ### Metrics and Stats ###
        stats = self.get_api_data(self.base_api)['pool']
        
        last_block_found = stats['lastPoolBlockTime']
        format_string = '%Y-%m-%dT%H:%M:%S.%fZ'
        date_time_obj = datetime.strptime(last_block_found, format_string)
        last_block_found = date_time_obj.strftime('%A, %B %d, %Y at %I:%M:%S %p')
        # pool_effort = stats['poolEffort']
        
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
        

        ### BLOCK STATS ###
        url = '{}/{}'.format(self.base_api, 'blocks?pageSize=5000')
        block_data = self.get_api_data(url)
        block_df = DataFrame(block_data)
        
        try:
            block_df['Time Found'] = to_datetime(block_df['created'])
            block_df['Time Found'] = block_df['Time Found'].dt.strftime('%Y-%m-%d %H:%M:%S')
        except KeyError:
            block_df['Time Found'] = 'Not Found Yet'
        
        try:
            block_df['effort [%]'] = round(block_df['effort'] * 100, 3)
        except KeyError:
            block_df['miner'] = 'NONE'
            block_df['effort [%]'] = 'NONE'
            block_df['networkDifficulty'] = 0

        block_df['Rolling Effort'] = block_df['effort [%]'].expanding().mean()
        block_df['Confirmation [%]'] = round(block_df['confirmationProgress'] * 100, 3)
        block_df['reward [erg]'] = block_df['reward']
        
        self.block_df = block_df

        self.latest_block = max(block_df['Time Found'])
        
        ### EFFORT AND TTF ###
        self.data['poolEffort'] = self.calculate_mining_effort(self.data['networkDifficulty'], self.data['networkHashrate'],
                                                            self.data['poolHashrate'] * 1e3, self.latest_block)
        
        self.data['poolTTF'] = self.calculate_time_to_find_block(self.data['networkDifficulty'], self.data['networkHashrate'],
                                                              self.data['poolHashrate'] * 1e3, self.latest_block)
        ### TOTAL HASH ####
        all_miner_samples = [self.get_miner_samples(miner) for miner in miner_ls]
        
        self.miner_sample_df = concat(all_miner_samples)
        # self.miner_sample_df['miner'] = self.miner_sample_df['miner'].apply(lambda x: f"{x[:5]}...{x[-5:]}" if len(x) > 10 else x)
        self.latest_snapshot = max(self.miner_sample_df.created)
        self.miner_sample_df['hashrate'] = round(self.miner_sample_df['hashrate'] / 1e6, 3)
        self.miner_sample_df['sharesPerSecond'] = round(self.miner_sample_df['sharesPerSecond'], 3)
        
        self.miner_latest_samples = self.miner_sample_df[self.miner_sample_df.created == self.latest_snapshot]
        

    def get_miner_payment_stats(self, wallet):
        # MINING PAGE
        url = '{}/{}/{}'.format(self.base_api, 'miners', wallet)
        mining_data = self.get_api_data(url)
        

        try:
            payment_dict = {'Pending Shares': round(mining_data['pendingShares'], 3),
                           'Pending Balance': round(mining_data['pendingBalance'], 3),
                           'Total Paid': round(mining_data['totalPaid'], 3),
                           'Paid Today': mining_data['todayPaid'],
                           'Schema': 'PPLNS',
                           'Price': self.erg_price}
        except:
            payment_dict = {'Pending Shares': 0,
                           'Pending Balance': 0,
                           'Paid Today': 0,
                           'Paid Today': 0,
                           'Schema': 'PPLNS',
                           'Price': self.erg_price}
            
        # MINERS NOT PAID YET EXCEPTIONS
        try:
            payment_dict['Last Payment'] = mining_data['lastPayment'][:-17]
            payment_dict['lastPaymentLink'] = mining_data['lastPaymentLink']
        
        except KeyError: 
            payment_dict['Last Payment'] = 0
            payment_dict['lastPaymentLink'] = 'Keep Mining!'

        except TypeError:
            payment_dict['Last Payment'] = 0
            payment_dict['lastPaymentLink'] = 'Keep Mining!'

        return payment_dict

    def get_latest_worker_samples(self, totals=False):
        '''
        This function is to be used for individual Miner work stats and Total MINER STATS
        '''
   
        df = self.miner_latest_samples

        total_ls = []
        work_ls = []
        block_df = self.block_df
        
        for miner in df.miner.unique():                
            temp = df[df.miner == miner]
            temp_block = block_df[block_df.miner == miner]
            try:
                temp_latest = max(temp_block['Time Found'])
            except ValueError:
                temp_latest = min(block_df['Time Found'])

            if not isinstance(temp_latest, str):
                temp_latest = max(temp_block['Time Found'])

            
           
            temp_hash = round(temp.hashrate.sum(), 0)
            effort = self.calculate_mining_effort(self.data['networkDifficulty'], self.data['networkHashrate'], temp_hash, temp_latest)
            ttf = self.calculate_time_to_find_block(self.data['networkDifficulty'], self.data['networkHashrate'], temp_hash, temp_latest)
            temp['Last Block Found'] = temp_latest
            temp['Effort'] = [self.calculate_mining_effort(self.data['networkDifficulty'], self.data['networkHashrate'], hash, temp_latest) for hash in temp.hashrate]
            temp['TTF'] = [self.calculate_time_to_find_block(self.data['networkDifficulty'], self.data['networkHashrate'], hash, temp_latest) for hash in temp.hashrate]
            work_ls.append(temp)
            total_ls.append([miner, temp_hash, round(temp.sharesPerSecond.sum(), 2), effort, ttf, temp_latest])   
        
        if totals:
            df = DataFrame(total_ls, columns=['Miner', 'Hashrate', 'SharesPerSecond', 'Effort', 'TTF', 'Last Block Found'])
            df['Miner'] = df['Miner'].apply(lambda x: f"{x[:5]}...{x[-5:]}" if len(x) > 10 else x)
            return df

        return concat(work_ls)
        
        
    def get_total_hash_data(self):
        '''
        This function is to be used for the Front Page Hashrate over Time
        '''
        total_hash = []
        for date in self.miner_sample_df.created.unique():
            
            temp = self.miner_sample_df[self.miner_sample_df.created == date]
            total_hash.append([date, temp.hashrate.sum() / 1e3])

        # DF FOR PLOTTING TOTAL HASH ON FRONT PAGE
        total_hash_df = DataFrame(total_hash, columns=['Date', 'Hashrate'])
        return total_hash_df
 
    def get_miner_ls(self):
        data = self.get_api_data('{}/{}'.format(self.base_api, 'miners'))
        miner_ls = []
        for sample in data:
            miner_ls.append(sample['miner'])
    
        return miner_ls      
    
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
            
    def get_miner_samples(self, wallet):
        #
        url = '{}/{}/{}'.format(self.base_api, 'miners', wallet)
        sample_data = self.get_api_data(url)
        try:
            samples = sample_data['performanceSamples']
        except TypeError:
            return DataFrame({'created': [0], 'hashrate': [0], 'worker': ['not loaded']})

        flattened_data = []
    
        for entry in samples:
            created_time = entry['created']
            
            for worker_name, metrics in entry['workers'].items():
                
                flat_entry = {
                    'created': created_time,
                    'worker': worker_name,
                    'hashrate': metrics['hashrate'],
                    'sharesPerSecond': metrics['sharesPerSecond'],
                    'miner': wallet
                }

                flattened_data.append(flat_entry)
        df = DataFrame(flattened_data)

        if df.empty:
            df = DataFrame({'created': [0], 'hashrate': [0], 'worker': ['not loaded']})
    
        return df


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

    def calculate_time_to_find_block(self, network_difficulty, network_hashrate, hashrate, last_block_timestamp):
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
    
        # Parse the last block timestamp
        time_format = '%Y-%m-%d %H:%M:%S' 
        last_block_time = datetime.strptime(last_block_timestamp, time_format)
        last_block_time = last_block_time.replace(tzinfo=pytz.utc)  # Assume the timestamp is in UTC
        
        # Get the current time in UTC
        now = datetime.now(pytz.utc)
        
        # Calculate the time difference in seconds
        time_since_last_block = (now - last_block_time).total_seconds()
        
        # Hashes to find a block at current difficulty
        hashes_to_find_block = network_difficulty  # This is a simplification
        
        # Calculate the time to find a block
        # print(hashrate, 'hashhh', hashes_to_find_block)
        try:
            time_to_find_block = hashes_to_find_block / hashrate
        except ZeroDivisionError:
            time_to_find_block = 1
        
        return round(time_to_find_block / 3600 / 24, 3)

            
    def find_token_in_wallet(self, wallet):
        url = '{}/{}'.format(self.api, wallet)
        wallet_data = self.get_api_data(url)

        wallet_contents = wallet_data['items']
        for contents in wallet_contents:
            if contents['assets']:
                for items in contents['assets']:
                    token_id = items['tokenId']
                    if token_id == self.token_id:
                        return True
                        
    def get_token_description(self):
        url = '{}/{}'.format(self.token_ls, self.token_id)
        data = self.get_api_data(url)

        token_description = data['description']
        return token_description
