import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from pycoingecko import CoinGeckoAPI
from datetime import datetime
from hydra.core.global_hydra import GlobalHydra

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
        self.block_reward = 30
        self.config_path = config_path
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

    def get_miner_ls(self):
        data = self.get_api_data('{}/{}'.format(self.base_api, 'miners'))
        miner_ls = []
        for sample in data:
            miner_ls.append(sample['miner'])
    
        return miner_ls

    def get_front_page_data(self):
        pool = self.get_api_data(self.base_api)['pool']
        
        payment_data = pool['paymentProcessing'] # dict

        port_data = pool['ports']

        ls = []
        for port in port_data:
            temp = port_data[port]
            if 'pikes_peak' in temp['name']:
                high_or_low = 'Greater Than 10GH/s'
            else:
                high_or_low = 'Lower Than 10GH/s'
            ls.append([temp['name'], port, high_or_low, temp['tls']])
        port_df = DataFrame(ls, columns=['Name', 'Port', 'Hashrate Threshold', 'TLS'])

        pool_fee = pool['poolFeePercent']
        pool_stats = pool['poolStats'] # dict
        net_stats = pool['networkStats'] # dict
     
        total_paid = pool['totalPaid']
        total_blocks = pool['totalBlocks']
        last_block_found = pool['lastPoolBlockTime']

        format_string = '%Y-%m-%dT%H:%M:%S.%fZ'

        date_time_obj = datetime.strptime(last_block_found, format_string)
        last_block_found = date_time_obj.strftime('%A, %B %d, %Y at %I:%M:%S %p')
        
        pool_effort = pool['poolEffort']

        data = {'port_df': port_df,
                'fee': pool_fee,
                'paid': total_paid,
                'blocks': total_blocks,
                'last_block_found': last_block_found,
                'pool_effort': pool_effort}
        
        

        for key in payment_data.keys():
            data[key] = payment_data[key]

        for key in pool_stats.keys():
            data[key] = pool_stats[key]

        for key in net_stats.keys():
                data[key] = net_stats[key]

        data['poolHashrate'] = data['poolHashrate'] / 1e9 # GigaHash/Second
        data['networkHashrate'] = data['networkHashrate'] / 1e12 # Terra Hash/Second
        data['networkDifficulty'] = data['networkDifficulty'] / 1e15 # Peta

        # date_time_obj = datetime.strptime(data['lastNetworkBlockTime'], format_string)
        # data['lastNetworkBlockTime'] = date_time_obj.strftime('%A, %B %d, %Y at %I:%M:%S %p')

        # self.pool_hash = data['poolHashrate']
        # self.net_hash = data['networkHashrate']
        # self.net_diff = data['network_difficulty']
        return data

    def get_main_page_metrics(self, wallet, debug=False):
        ''' btc_price, erg_price, your_total_hash, pool_hash, network_hashrate, avg_block_effort, network_difficulty '''
        price_reader = PriceReader()
        btc, erg = price_reader.get(debug)
        _, performance_df = self.get_mining_stats(wallet)
        _, _, effort_df = self.get_block_stats(wallet)
        data = self.get_front_page_data()
        pool_hash = data['poolHashrate']
        net_hash = data['networkHashrate']
        net_diff = data['networkDifficulty']
        your_total_hash = round(performance_df[performance_df['Worker'] == 'Totals']['Hashrate [Mh/s]'].iloc[0], 5)
        avg_block_effort = round(effort_df[effort_df['Mining Stats'] == 'Average Block Effort']['Values'].iloc[0], 5)
        return btc, erg, your_total_hash, pool_hash, net_hash, avg_block_effort, net_diff

        
        
    
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
            
    def get_estimated_payments(self, wallet):
        url = '{}/{}'.format(self.base_api, 'miners')
        miner_data = self.get_api_data(url)

        miners = {}
        for sample in miner_data:
            miners[sample['miner']] = 0
            
        for key in miners.keys():
            unique_miner_url = '{}/{}'.format(url, key)
            sample_miner = self.get_api_data(unique_miner_url)
            miners[key] = sample_miner['pendingShares']
            
        total = sum(miners.values())
        rewards = {key: (value / total) * self.block_reward  for key, value in miners.items()}
        reward_df = DataFrame(list(rewards.items()), columns=['miner', 'reward'])
        reward_df['my_wallet'] = reward_df['miner'].apply(lambda address: address == wallet)
        
        return reward_df

    def get_miner_samples(self, wallet):
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
                    'sharesPerSecond': metrics['sharesPerSecond']
                }

                flattened_data.append(flat_entry)
        df = DataFrame(flattened_data)

        if df.empty:
            df = DataFrame({'created': [0], 'hashrate': [0], 'worker': ['not loaded']})
    
        return df

                    
    def get_mining_stats(self, wallet):
        url = '{}/{}/{}'.format(self.base_api, 'miners', wallet)
        mining_data = self.get_api_data(url)
        # WALLET NOT ADDED EXCEPTIONS
        try:
            mining_dict = {'pendingShares': mining_data['pendingShares'],
                           'pendingBalance': mining_data['pendingBalance'],
                           'totalPaid': mining_data['totalPaid'],
                           'todayPaid': mining_data['todayPaid']}
        except:
            mining_dict = {'pendingShares': 0,
                           'pendingBalance': 0,
                           'totalPaid': 0,
                           'todayPaid': 0}
            
        # MINERS NOT PAID YET EXCEPTIONS
        try:
            mining_dict['lastPayment'] = mining_data['lastPayment']
            mining_dict['lastPaymentLink'] = mining_data['lastPaymentLink']
        
        except KeyError: 
            mining_dict['lastPayment'] = 0
            mining_dict['lastPaymentLink'] = 'Keep Mining!'

        except TypeError:
            mining_dict['lastPayment'] = 0
            mining_dict['lastPaymentLink'] = 'Keep Mining!'

        # EXCEPTION LOGIC FOR USERS TO INPUT THEIR ADDRESS
        try:
            performance = mining_data['performance']
            performance_df = DataFrame(performance['workers']).T  # Transpose to get workers as rows
            performance_df.reset_index(inplace=True)  # Reset index to get workers as a column
            performance_df.columns = ['Worker', 'Hashrate [Mh/s]', 'SharesPerSecond']  # Rename columns
            performance_df['Hashrate [Mh/s]'] = performance_df['Hashrate [Mh/s]'] / 1e6 # MH/s
        except:
            print('NO VALID WALLET ENTERED'.format(wallet))
          
            performance = 'PLEASE ENTER YOUR MINING WALLET ADDRESS'
            performance_df = DataFrame()
            performance_df['Hashrate [Mh/s]'] = 0
            performance_df['SharesPerSecond'] = 1e-6
        
        total_hash = sum(performance_df['Hashrate [Mh/s]'])
        total_shares = sum(performance_df['SharesPerSecond'])

        temp = DataFrame({'Worker': 'Totals', 'Hashrate [Mh/s]': total_hash, 'SharesPerSecond': total_shares}, index=[0])

        performance_df = concat([performance_df, temp])
        
        mining_df = DataFrame.from_dict(mining_dict, orient='index', columns=['Value'])
        mining_df.reset_index(inplace=True)
        mining_df.columns = ['Mining Stats', 'Values']

        return mining_df, performance_df

    def get_block_stats(self, wallet):
        url = '{}/{}'.format(self.base_api, 'Blocks')
        block_data = self.get_api_data(url)

        miners = {}
        blocks = {}
        for block in block_data:
            miner = block['miner']
            block_height = block['blockHeight']

            try:
                miners[miner] += 1
            except KeyError:
                miners[miner] = 1
            blocks[block_height] = block['effort']
        try:
            average_effort = {'Average Block Effort': sum(blocks.values()) / len(blocks)}
        except ZeroDivisionError:
            average_effort = {'Average Block Effort': 0}

        block_df = DataFrame(block_data)
        
        miner_df = DataFrame.from_dict(miners, orient='index', columns=['Value'])
        miner_df.reset_index(inplace=True)
        miner_df.columns = ['miner', 'Number of Blocks Found']
        
        try:
            block_df['my_wallet'] = block_df['miner'].apply(lambda address: address == wallet)
            miner_df['my_wallet'] = miner_df['miner'].apply(lambda address: address == wallet)
            
        except ValueError:
            print('my wallet_value errr')
            block_df['my_wallet'] = 'NOT ENTERED'
            miner_df['my_wallet'] = 'NOT ENTERED'

        except KeyError:
            block_df['my_wallet'] = 'NONE'
            miner_df['my_wallet'] = 'NONE'
        
        miner_df['miner'] = miner_df['miner'].apply(lambda x: f"{x[:5]}...{x[-5:]}" if len(x) > 10 else x)


        effort_df = DataFrame.from_dict(average_effort, orient='index', columns=['Values'])
        effort_df.reset_index(inplace=True)
        effort_df.columns = ['Mining Stats', 'Values']
        
        try:
            block_df['Time Found'] = to_datetime(block_df['created'])
            block_df['Time Found'] = block_df['Time Found'].dt.strftime('%Y-%m-%d %H:%M:%S')
        except KeyError:
            block_df['Time Found'] = 'Not Found Yet'
        
        try:
            block_df['miner'] = block_df['miner'].apply(lambda x: f"{x[:5]}...{x[-5:]}" if len(x) > 10 else x)
            block_df['effort'] = round(block_df['effort'], 5)
        except KeyError:
            block_df['miner'] = 'NONE'
            block_df['effort'] = 'NONE'
            block_df['networkDifficulty'] = 0
        
    
        block_df = block_df.filter(['Time Found', 'blockHeight', 'effort', 'status', 'confirmationProgress', 'reward', 
                                    'miner', 'networkDifficulty', 'my_wallet'])

        
        return block_df, miner_df, effort_df

    def get_pool_stats(self, wallet):
        data = self.get_api_data(self.base_api)
        pool_data = data['pool']['poolStats']
        net_data = data['pool']['networkStats']
        net_data['networkHashrate'] = net_data['networkHashrate'] / 1e12 
        net_data['networkHashrate [Th/s]'] = net_data.pop('networkHashrate')

        net_data['networkDifficulty'] = net_data['networkDifficulty'] / 1e15 
        net_data['networkDifficulty [Peta]'] = net_data.pop('networkDifficulty')

        pool_data['poolHashrate'] = pool_data['poolHashrate'] / 1e9
        pool_data['poolHashrate [Gh/s]'] = pool_data.pop('poolHashrate')
        
        top_miner_data = data['pool']['topMiners']

        pool_df = DataFrame(list(pool_data.items()), columns=['Key', 'Value'])
        net_df = DataFrame(list(net_data.items()), columns=['Key', 'Value'])
        
        df = concat([pool_df, net_df], ignore_index=True)
        df.columns = ['Pool Stats', 'Values']
        
        top_miner_df = DataFrame(top_miner_data)
        top_miner_df['my_wallet'] = top_miner_df['miner'].apply(lambda address: address == wallet)
        top_miner_df['miner'] = top_miner_df['miner'].apply(lambda x: f"{x[:5]}...{x[-5:]}" if len(x) > 10 else x)
        top_miner_df['hashrate'] = top_miner_df['hashrate'] / 1e6 # Mh/s
        
        total_hash = top_miner_df['hashrate'].sum()
        top_miner_df['Percentage'] = (top_miner_df['hashrate'] / total_hash) * 100
        top_miner_df['ProjectedReward'] = (top_miner_df['Percentage'] / 100) * self.block_reward
        return df, top_miner_df
            
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
