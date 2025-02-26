import requests
import json 
import logging

logger = logging.getLogger(__name__)

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
                logger.error(f"Failed to retrieve data: Status code {response.status_code}")
                return None
    
        except requests.exceptions.RequestException as e:
            # Handle any exceptions that occur during the request
            logger.error(f"An error occurred: {e}")
            return None
            
    def get_wallet_balance(self, wallet_json):
        try:
            # Parse the wallet JSON to get the address
            wallet_data = json.loads(wallet_json)
            if not wallet_data.get('addresses'):
                logger.error("No addresses found in wallet data")
                return None
                
            address = wallet_data['addresses'][0]
            
            # Use the Ergo Explorer API to get balance and tokens
            url = f'https://api.ergoplatform.com/api/v1/addresses/{address}/balance/confirmed'
            
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Convert the response to match the expected format
                return {
                    'confirmed': {
                        'tokens': data.get('tokens', [])
                    }
                }
            else:
                logger.error(f"Failed to get wallet balance: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return None

    def find_token_name_in_wallet(self, wallet, name):
        try:
            wallet_data = self.get_wallet_balance(wallet)
            if not wallet_data:
                logger.error("No wallet data received")
                return []
                
            if 'error' in wallet_data:
                logger.error(f"API error: {wallet_data['error']} - {wallet_data.get('detail', '')}")
                return []
                
            if 'confirmed' not in wallet_data:
                logger.error("No confirmed data in wallet response")
                return []
                
            if 'tokens' not in wallet_data['confirmed']:
                logger.error("No tokens data in wallet response")
                return []

            tokens = wallet_data['confirmed']['tokens']
            ls = []
            for token in tokens:
                token_name = token.get('name')
                if token_name == name:
                    ls.append(token)
            return ls
        except Exception as e:
            logger.error(f"Error finding tokens: {e}")
            return []

    def get_latest_miner_id(self, wallet):
        possible_tokens = self.find_token_name_in_wallet(wallet, 'Sigmanaut Mining Pool Miner ID - Season 1')

        my_tokens = []
        most_recent_token = None
        highest_creation_height = 0
        
        for token in possible_tokens:
            token_id = token['tokenId']
            print(token_id, 'id')
            
            # Get boxes by token ID
            boxes_url = f'https://api.ergoplatform.com/api/v1/boxes/byTokenId/{token_id}'
            boxes_data = self.get_api_data(boxes_url)
            
            # Find the earliest transaction for this token
            earliest_tx = min(boxes_data['items'], key=lambda x: x['creationHeight'])
            earliest_tx_id = earliest_tx['transactionId']
            
            # Get transaction details
            tx_url = f'https://api.ergoplatform.com/api/v1/transactions/{earliest_tx_id}'
            tx_data = self.get_api_data(tx_url)
            
            box_id_first_input = tx_data['inputs'][0]['boxId']
            
            # Check outputs for minting information
            for output in tx_data['outputs']:
                assets = output.get('assets', [])
                if assets and assets[0]['tokenId'] == box_id_first_input:
                    minting_address = output['address']
                    creation_height = output['creationHeight']
                    
                    if minting_address == wallet:
                        my_tokens.append(token)
                        if creation_height > highest_creation_height:
                            highest_creation_height = creation_height
                            most_recent_token = token
                    break  # Found the minting output for this token, move to next token

        return most_recent_token
                                    
    def get_token_description(self, id):
        url = '{}/{}'.format(self.token_ls, id)
        data = self.get_api_data(url)
        if not data:
            return None
            
        try:
            # The description field is a JSON string that needs to be parsed
            description_str = data.get('description')
            if not description_str:
                logger.error(f"No description field found in token data: {data}")
                return None
                
            return json.loads(description_str)
        except Exception as e:
            logger.error(f"Error parsing token description: {e}")
            return None
