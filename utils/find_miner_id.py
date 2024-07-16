import requests
import json 

class ReadTokens:
    def __init__(self, api='https://api.ergo.aap.cornell.edu/api/v1/boxes/byAddress', token_ls_url='https://api.ergo.aap.cornell.edu/api/v1/tokens/'):
        '''
        This code does a few things to find the latest miners ID:
        1. First we get the miners address and search for some known parameters that should be in the token
        2. From here we then look at block of when the token was first minted
        3. Then we check to see if miners address (current hold) was the address that minted this token

        '''
        
        self.api = api
        self.token_ls = token_ls_url

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
            
    def get_wallet_balance(self, wallet):
        url = 'http://213.239.193.208:9053/blockchain/balance'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(url, headers=headers, data=wallet)
        return response.json()

    
    def find_token_name_in_wallet(self, wallet, name):
        wallet_data = self.get_wallet_balance(wallet)

        tokens = wallet_data['confirmed']['tokens']
        ls = []
        for token in tokens:
            token_name = token['name']
            if token_name == name:
                ls.append(token)
        return ls

    def get_latest_miner_id(self, wallet):
        possible_tokens = self.find_token_name_in_wallet(wallet, 'Sigmanaut Mining Pool Miner ID - Season 0')

        my_tokens = []
        miner_id = None
        for token in possible_tokens:
            
            id = token['tokenId']
            base_url = 'https://api.ergoplatform.com/api/v1/boxes/byTokenId'
            url = '{}/{}'.format(base_url, id)
            data = self.get_api_data(url)
            oldest_height = 1e30
            # for a given token we want to find the earliest TX with it so we can see who minted it
            for item in data['items']:
                if oldest_height > item['creationHeight']:
                    oldest_height = item['creationHeight']
                    # ls = item['boxId'], item['creationHeight'], item['transactionId'], item['address']
                    tx = item['transactionId']
            
            # tx = ls[2]
            wallet_minted_tokens = []
            url = 'https://api.ergoplatform.com/api/v1/transactions'
            tx_url = '{}/{}'.format(url, tx)
            data = self.get_api_data(tx_url)
            # print(data)
            box_id_first_input = data['inputs'][0]['boxId']
        
            outputs = data['outputs']
            # print(outputs, 'oi')
            earliest_height = 0
            for sample in outputs:
                try:   
                    assets = sample['assets'][0]
                    if assets['tokenId'] == box_id_first_input:
                        minting_address = sample['address']
                        if wallet == minting_address:
                            if sample['creationHeight'] > earliest_height:
                                oldest_height = sample['creationHeight']
                                my_tokens.append(token)
                                miner_id = token
                            break
                except IndexError:
                    pass
        return miner_id
                                    
    def get_token_description(self, id):
        url = '{}/{}'.format(self.token_ls, id)
        data = self.get_api_data(url)

        token_description = json.loads(data['description'])
        return token_description

