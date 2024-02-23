import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf

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

        token_in_wallet = self.find_token_in_wallet()
        if token_in_wallet:
            description = self.get_token_description()
            print('THE ADDRESS {} CONTAINS THE TOKEN {} WITH THE DESCRIPTION OF {}'.format(self.wallet, self.token_id, description))
            return description
        else:
            print('THE ADDRESS {} DOES NOT CONTAIN THE TOKEN {}'.format(self.wallet, self.token_id))   

if __name__ == '__main__':
    runner = SigmaWalletReader(config_path='conf')
    runner.run_app()