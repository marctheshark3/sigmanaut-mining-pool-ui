import requests

class ReadTokens:
    def __init__(self, api, token_ls_url='https://api.ergo.aap.cornell.edu/api/v1/tokens/'):
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
         

    # def find_miner_id(self, wallet):
    #     url = '{}/{}'.format(self.api, wallet)
    #     wallet_data = self.get_api_data(url)

    #     wallet_contents = wallet_data['items']
    #     # print(wallet_contents)
    #     miner_ids = []
    #     for contents in wallet_contents:
    #         if contents['assets']:
    #             for items in contents['assets']:
    #                 # print(items)
    #                 token_id = items['tokenId']
    #                 if items['name'] == 'Sigmanaut Mining Pool Miner ID - Season 0':
    #                     miner_ids.append(token_id) 
                    
    #     return miner_ids

    def get_latest_miner_id(self, wallet):
        possible_tokens = self.find_token_name_in_wallet(wallet, 'Sigmanaut Mining Pool Miner ID - Season 0')
        for token in possible_tokens:
            id = token['tokenId']
            url = 'https://api.ergoplatform.com/api/v1/boxes/byTokenId/a24b57a4b9a8122a52c5d92a6250b7ed5df134e660f3e3946770858a3fc46eb7'
            # url = 'https://api.ergoplatform.com/api/v1/boxes/byTokenId/5104822ac703509fb6790961d8d2b4afa4c75b9514abfd48ca8bf83639d30574'
            data = find_tokens.get_api_data(url)
            
            ls = []
            oldest_height = 1e30
            for item in data['items']:
                print(item['creationHeight'])
                if oldest_height > item['creationHeight']:
                    oldest_height = item['creationHeight']
                    ls = item['boxId'], item['creationHeight'], item['transactionId'], item['address']
                # ls.append([item['boxId'], item['creationHeight'], item['transactionId'], item['address']])
            
            tx = ls[2]
            url = 'https://api.ergoplatform.com/api/v1/transactions'
            tx_url = '{}/{}'.format(url, tx)
            data = find_tokens.get_api_data(tx_url)
            box_id_first_input = data['inputs'][0]['boxId']

            outputs = data['outputs']

            for sample in outputs:
                assets = sample['assets'][0]
                if assets['tokenId'] == box_id_first_input:
                    minting_address = sample['address']
                    break
            
            minting_address
                                    
    def get_token_description(self, id):
        url = '{}/{}'.format(self.token_ls, id)
        data = self.get_api_data(url)

        token_description = data['description']
        return token_description, data

    # def get_latest_miner_id(self, wallet):
    #     tokens = self.find_token_name_in_wallet(wallet)
    #     max_height = 0
    #     latest_id = {}
    #     for token in tokens:
    #         id = token['tokenId']
    #         token_description, _ = self.get_token_description(id)
    #         data = eval(token_description)
    #         if max_height < int(data['height']) and wallet == data['address']:
    #             max_height = data['height']
    #             latest_id = data
    #             # latest_id['token_id'] = id
    #     return latest_id


if __name__ == '__main__':
    url = 'https://api.ergo.aap.cornell.edu/api/v1/boxes/byAddress/'
    wallet = '9eg7v2nkypUZbdyvSKSD9kg8FNwrEdTrfC2xdXWXmEpDAFEtYEn'
    reader = ReadTokens(url, token_id)

    ids = reader.find_miner_id(wallet)
