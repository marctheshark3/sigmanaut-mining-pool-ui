import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat

class SigmaWalletReader:
    # def __init__(self, api, token_id, token_ls_url='https://api.ergo.aap.cornell.edu/api/v1/tokens/'):
    #     self.api = api
    #     self.token_id = token_id
    #     self.token_ls = token_ls_url

    def __init__(self, config_path: str):
        self.config_path = config_path
        
        initialize(config_path, self.config_path, version_base=None)
        cfg = compose(config_name='conf')

        self.api = cfg.default_values.url
        self.token_id = cfg.user_defined.token_id
        self.token_ls = cfg.default_values.token_ls
        self.wallet = cfg.user_defined.wallet
        self.base_api = cfg.default_values.base_api
    
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
            
    def get_mining_stats(self):
        url = '{}/{}/{}'.format(self.base_api, 'miners', self.wallet)
        mining_data = self.get_api_data(url)

        mining_dict = {'pendingShares': mining_data['pendingShares'],
                       'pendingBalance': mining_data['pendingBalance'],
                       'totalPaid': mining_data['totalPaid'],
                       'todayPaid': mining_data['todayPaid'],
                       'lastPayment': mining_data['lastPayment'],
                       'lastPaymentLink': mining_data['lastPaymentLink'],}

        performance = mining_data['performance']
        performance_df = DataFrame(performance['workers']).T  # Transpose to get workers as rows
        performance_df.reset_index(inplace=True)  # Reset index to get workers as a column
        performance_df.columns = ['Worker', 'Hashrate [Mh/s]', 'SharesPerSecond']  # Rename columns
        performance_df['Hashrate [Mh/s]'] = performance_df['Hashrate [Mh/s]'] / 1e6 # MH/s
        
        mining_df = DataFrame.from_dict(mining_dict, orient='index', columns=['Value'])
        mining_df.reset_index(inplace=True)
        mining_df.columns = ['Mining Stats', 'Values']

        return mining_df, performance_df

    def get_block_stats(self):
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

        average_effort = {'Average Block Effort': sum(blocks.values()) / len(blocks)}

        block_df = DataFrame(block_data)
        block_df['my_wallet'] = block_df['miner'].apply(lambda address: address == self.wallet)
        # block_df['networkDifficulty'] = block_df['networkDifficulty'] / 1e15 

        miner_df = DataFrame.from_dict(miners, orient='index', columns=['Value'])
        miner_df.reset_index(inplace=True)
        miner_df.columns = ['Miner', 'Number of Blocks Found']
        miner_df['my_wallet'] = miner_df['Miner'].apply(lambda address: address == self.wallet)

        effort_df = DataFrame.from_dict(average_effort, orient='index', columns=['Values'])
        effort_df.reset_index(inplace=True)
        effort_df.columns = ['Mining Stats', 'Values']
        
        return block_df, miner_df, effort_df

    def get_pool_stats(self):
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
        
        # Concatenate the two DataFrames
        df = concat([pool_df, net_df], ignore_index=True)
        df.columns = ['Pool Stats', 'Values']
        

        top_miner_df = DataFrame(top_miner_data)
        top_miner_df['my_wallet'] = top_miner_df['miner'].apply(lambda address: address == self.wallet)

        return df, top_miner_df
        
            
    def find_token_in_wallet(self):
        url = '{}/{}'.format(self.api, self.wallet)
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

    def run_app(self):
        '''
        block data contains a all of the blocks found by the pool, a count of the miners that found a block, and average effort calculation

        mining_data contains various mining metrics for a given miner

        pool_data contain pool data, network stats, and the list of miners sorted by shares
        '''
        block_data = self.get_block_stats()
        mining_data = self.get_mining_stats()
        pool_data = self.get_pool_stats()
        return block_data, mining_data, pool_data
