import requests

class ReadTokens:
    def __init__(self, api, token_ls_url='https://api.ergo.aap.cornell.edu/api/v1/tokens/'):
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

    def find_token_in_wallet(self, wallet, id):
        url = '{}/{}'.format(self.api, wallet)
        wallet_data = self.get_api_data(url)

        wallet_contents = wallet_data['items']
        for contents in wallet_contents:
            
            if contents['assets']:
                for items in contents['assets']:
                    print(items)
                    token_id = items['tokenId']
                    print(token_id)
                    if token_id == id:
                        return True
        return False

    def find_miner_id(self, wallet):
        url = '{}/{}'.format(self.api, wallet)
        wallet_data = self.get_api_data(url)

        wallet_contents = wallet_data['items']
        miner_ids = []
        for contents in wallet_contents:
            if contents['assets']:
                for items in contents['assets']:
                    print(items)
                    token_id = items['tokenId']
                    if items['name'] == 'Sigmanaut Mining Pool Miner ID - Season 0':
                        miner_ids.append(token_id) 
                    
        return miner_ids
                        
    def get_token_description(self, id):
        url = '{}/{}'.format(self.token_ls, id)
        data = self.get_api_data(url)

        token_description = data['description']
        return token_description, data

    def get_latest_miner_id(self, wallet):
        miner_ids = self.find_miner_id(wallet)
        max_height = 0
        latest_id = {}
        for id in miner_ids:
            token_description, _ = self.get_token_description(id)
            data = eval(token_description)
            if max_height < int(data['height']) and wallet == data['address']:
                max_height = data['height']
                latest_id = data
                # latest_id['token_id'] = id
        return latest_id


if __name__ == '__main__':
    url = 'https://api.ergo.aap.cornell.edu/api/v1/boxes/byAddress/'
    wallet = '9eg7v2nkypUZbdyvSKSD9kg8FNwrEdTrfC2xdXWXmEpDAFEtYEn'
    reader = ReadTokens(url, token_id)

    ids = reader.find_miner_id(wallet)
