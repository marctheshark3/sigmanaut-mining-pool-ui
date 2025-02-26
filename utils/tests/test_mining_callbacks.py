import unittest
from unittest.mock import patch, MagicMock
import json
import logging
from ..mining_callbacks import get_minimum_payout
from ..find_miner_id import ReadTokens

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestMiningCallbacks(unittest.TestCase):
    def setUp(self):
        self.test_address = "9gPohoQooaGWbZbgTb1JrrqFWiTpM2zBknEwiyDANwmAtAne1Y8"
        self.collection_id = "10ba19fae939a8c185eddb239d85f4dc8a77564cb6167578d8019f24696446fc"

    @patch('utils.mining_callbacks.ReadTokens')
    def test_get_minimum_payout_no_tokens(self, mock_read_tokens):
        # Setup mock for when no tokens are found
        mock_instance = MagicMock()
        mock_instance.find_token_name_in_wallet.return_value = []
        mock_read_tokens.return_value = mock_instance

        # Test the function
        result = get_minimum_payout(self.test_address)
        
        # Verify the result is the default value
        self.assertEqual(result, 0.5)
        
        # Verify the mock was called correctly
        expected_wallet_json = json.dumps({"addresses": [self.test_address]})
        mock_instance.find_token_name_in_wallet.assert_called_once_with(expected_wallet_json, 'Sigma BYTES')

    @patch('utils.mining_callbacks.ReadTokens')
    def test_get_minimum_payout_with_valid_token(self, mock_read_tokens):
        # Setup mock for valid token scenario
        mock_instance = MagicMock()
        test_token_id = "test_token_123"
        mock_instance.find_token_name_in_wallet.return_value = [{"tokenId": test_token_id}]
        
        # Create a valid token description
        valid_token_description = {
            "collection_id": self.collection_id,
            "type": "Pool Config",
            "address": self.test_address,
            "minimumPayout": "1.5"
        }
        mock_instance.get_token_description.return_value = valid_token_description  # Return dictionary directly
        mock_read_tokens.return_value = mock_instance

        # Test the function
        result = get_minimum_payout(self.test_address)
        
        # Verify the result matches the token's minimum payout
        self.assertEqual(result, 1.5)
        
        # Verify the mocks were called correctly
        expected_wallet_json = json.dumps({"addresses": [self.test_address]})
        mock_instance.find_token_name_in_wallet.assert_called_once_with(expected_wallet_json, 'Sigma BYTES')
        mock_instance.get_token_description.assert_called_once_with(test_token_id)

    @patch('utils.mining_callbacks.ReadTokens')
    def test_get_minimum_payout_with_invalid_token(self, mock_read_tokens):
        # Setup mock for invalid token scenario
        mock_instance = MagicMock()
        test_token_id = "test_token_123"
        mock_instance.find_token_name_in_wallet.return_value = [{"tokenId": test_token_id}]
        
        # Create an invalid token description (wrong collection_id)
        invalid_token_description = {
            "collection_id": "wrong_collection_id",
            "type": "Pool Config",
            "address": self.test_address,
            "minimumPayout": "1.5"
        }
        mock_instance.get_token_description.return_value = invalid_token_description  # Return dictionary directly
        mock_read_tokens.return_value = mock_instance

        # Test the function
        result = get_minimum_payout(self.test_address)
        
        # Verify the result is the default value since token was invalid
        self.assertEqual(result, 0.5)

    @patch('utils.mining_callbacks.ReadTokens')
    def test_get_minimum_payout_with_error(self, mock_read_tokens):
        # Setup mock to raise an exception
        mock_instance = MagicMock()
        mock_instance.find_token_name_in_wallet.side_effect = Exception("Test error")
        mock_read_tokens.return_value = mock_instance

        # Test the function
        result = get_minimum_payout(self.test_address)
        
        # Verify the result is the default value when an error occurs
        self.assertEqual(result, 0.5)

    def test_get_minimum_payout_live_address(self):
        """Test the get_minimum_payout function with a live address without mocking"""
        print("\n=== Starting Live Test ===")
        
        # Create ReadTokens instance directly for debugging
        tokens = ReadTokens()
        
        # Test wallet balance retrieval
        wallet_json = json.dumps({"addresses": [self.test_address]})
        print(f"\nChecking wallet balance for address: {self.test_address}")
        try:
            wallet_data = tokens.get_wallet_balance(wallet_json)
            print(f"Wallet data received: {json.dumps(wallet_data, indent=2)}")
        except Exception as e:
            print(f"Error getting wallet balance: {e}")
        
        # Test token search
        print("\nSearching for Sigma BYTES tokens...")
        try:
            found_tokens = tokens.find_token_name_in_wallet(wallet_json, 'Sigma BYTES')
            print(f"Found tokens: {json.dumps(found_tokens, indent=2)}")
            
            if found_tokens:
                for token in found_tokens:
                    print(f"\nGetting description for token: {token['tokenId']}")
                    try:
                        description = tokens.get_token_description(token['tokenId'])
                        print(f"Token description: {json.dumps(description, indent=2)}")
                    except Exception as e:
                        print(f"Error getting token description: {e}")
            
        except Exception as e:
            print(f"Error finding tokens: {e}")
        
        # Test the actual function
        print("\nTesting get_minimum_payout function...")
        result = get_minimum_payout(self.test_address)
        print(f"Final result: {result} ERG")
        
        # Verify the result
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
        print("\n=== Live Test Complete ===")

if __name__ == '__main__':
    unittest.main(verbosity=2) 