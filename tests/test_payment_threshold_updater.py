import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
from utils.update_payment_thresholds import PaymentThresholdUpdater

@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn, mock_cursor

@pytest.fixture
def updater(mock_db_connection):
    """Create PaymentThresholdUpdater instance with mocked dependencies"""
    mock_conn, _ = mock_db_connection
    with patch('utils.update_payment_thresholds.psycopg2.connect') as mock_connect:
        mock_connect.return_value = mock_conn
        updater = PaymentThresholdUpdater()
        updater._db_connection = mock_conn  # Set mocked connection
        return updater

def test_get_all_miners_success(updater):
    """Test successful retrieval of miners from API"""
    # Mock response data
    mock_miners = [
        {"address": "9f1234..."},
        {"address": "9f5678..."}
    ]
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_miners
        
        result = updater.get_all_miners()
        
        assert len(result) == 2
        assert result == mock_miners
        mock_get.assert_called_once_with(
            f"{updater.api_base_url}/sigscore/miners",
            params={"limit": 100, "offset": 0}
        )

def test_get_all_miners_pagination(updater):
    """Test pagination when getting miners from API"""
    # Mock response data for two pages
    page1 = [{"address": f"9f{i}..."} for i in range(100)]
    page2 = [{"address": f"9g{i}..."} for i in range(50)]
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [page1, page2]
        
        result = updater.get_all_miners()
        
        assert len(result) == 150
        assert mock_get.call_count == 2
        assert result[:100] == page1
        assert result[100:] == page2

def test_verify_nft_ownership_valid(updater):
    """Test NFT ownership verification with valid token"""
    token_info = {
        "collection_id": updater.collection_id,
        "type": "Pool Config",
        "address": "9f1234..."
    }
    
    assert updater.verify_nft_ownership(token_info, "9f1234...") is True

def test_verify_nft_ownership_invalid_collection(updater):
    """Test NFT ownership verification with invalid collection ID"""
    token_info = {
        "collection_id": "wrong_id",
        "type": "Pool Config",
        "address": "9f1234..."
    }
    
    assert updater.verify_nft_ownership(token_info, "9f1234...") is False

def test_verify_nft_ownership_invalid_type(updater):
    """Test NFT ownership verification with invalid type"""
    token_info = {
        "collection_id": updater.collection_id,
        "type": "Wrong Type",
        "address": "9f1234..."
    }
    
    assert updater.verify_nft_ownership(token_info, "9f1234...") is False

def test_verify_nft_ownership_wrong_address(updater):
    """Test NFT ownership verification with wrong address"""
    token_info = {
        "collection_id": updater.collection_id,
        "type": "Pool Config",
        "address": "9f1234..."
    }
    
    assert updater.verify_nft_ownership(token_info, "9f5678...") is False

@pytest.mark.parametrize("current_threshold,nft_threshold,should_update", [
    (0.1, 1.0, True),    # Different values should update
    (1.0, 1.0, False),   # Same values should not update
    (0.999999, 1.0, True),  # Small difference should update
])
def test_process_miner_threshold_update(updater, mock_db_connection, current_threshold, nft_threshold, should_update):
    """Test miner threshold processing with different scenarios"""
    mock_conn, mock_cursor = mock_db_connection
    address = "9f1234..."
    
    # Mock database queries
    mock_cursor.fetchone.return_value = (current_threshold,)
    
    # Mock NFT checks
    with patch.object(updater, 'get_miner_nft_threshold') as mock_get_nft:
        mock_get_nft.return_value = nft_threshold
        
        # Process single miner
        updater.process_all_miners([{"address": address}])
        
        # Verify database interactions
        if should_update:
            # Verify update was attempted
            update_calls = [call for call in mock_cursor.execute.call_args_list if 'UPDATE' in str(call)]
            assert len(update_calls) == 1
            update_call = update_calls[0]
            # Check if the parameters contain the expected values
            assert nft_threshold in update_call[0][1]  # Check parameters tuple
        else:
            # Verify no update was attempted (only SELECT)
            update_calls = [call for call in mock_cursor.execute.call_args_list if 'UPDATE' in str(call)]
            assert len(update_calls) == 0

def test_get_miner_nft_threshold_success(updater):
    """Test successful NFT threshold retrieval"""
    address = "9f1234..."
    token_id = "token123"
    expected_threshold = 1.5
    
    # Mock token reader responses
    with patch.object(updater.token_reader, 'find_token_name_in_wallet') as mock_find:
        mock_find.return_value = [{"tokenId": token_id}]
        
        with patch.object(updater.token_reader, 'get_token_description') as mock_desc:
            mock_desc.return_value = {
                "collection_id": updater.collection_id,
                "type": "Pool Config",
                "address": address,
                "minimumPayout": str(expected_threshold)
            }
            
            result = updater.get_miner_nft_threshold(address)
            
            assert result == expected_threshold
            mock_find.assert_called_once_with(
                json.dumps({"addresses": [address]}),
                'Sigma BYTES'
            )
            mock_desc.assert_called_once_with(token_id)

def test_get_miner_nft_threshold_no_tokens(updater):
    """Test NFT threshold retrieval with no tokens"""
    address = "9f1234..."
    
    with patch.object(updater.token_reader, 'find_token_name_in_wallet') as mock_find:
        mock_find.return_value = []
        
        result = updater.get_miner_nft_threshold(address)
        
        assert result is None

def test_integration_flow(updater, mock_db_connection):
    """Test the entire flow with mock data"""
    mock_conn, mock_cursor = mock_db_connection
    address = "9f1234..."
    current_threshold = 0.1
    new_threshold = 1.5
    
    # Mock database response
    mock_cursor.fetchone.return_value = (current_threshold,)
    
    # Mock NFT checks
    with patch.object(updater.token_reader, 'find_token_name_in_wallet') as mock_find:
        mock_find.return_value = [{"tokenId": "token123"}]
        
        with patch.object(updater.token_reader, 'get_token_description') as mock_desc:
            mock_desc.return_value = {
                "collection_id": updater.collection_id,
                "type": "Pool Config",
                "address": address,
                "minimumPayout": str(new_threshold)
            }
            
            # Process single miner
            updater.process_all_miners([{"address": address}])
            
            # Verify the flow
            mock_find.assert_called_once()
            mock_desc.assert_called_once()
            
            # Verify database operations
            select_calls = [call for call in mock_cursor.execute.call_args_list if 'SELECT' in str(call)]
            update_calls = [call for call in mock_cursor.execute.call_args_list if 'UPDATE' in str(call)]
            
            assert len(select_calls) == 1  # One SELECT for current threshold
            assert len(update_calls) == 1  # One UPDATE for new threshold
            
            # Verify update values
            update_call = update_calls[0]
            # Check if the parameters contain the expected values
            assert new_threshold in update_call[0][1]  # Check parameters tuple

if __name__ == '__main__':
    pytest.main([__file__]) 