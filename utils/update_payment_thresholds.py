import os
import logging
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from .find_miner_id import ReadTokens
import json
from typing import Optional, Dict, List
import time
import requests
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentThresholdUpdater:
    def __init__(self):
        """Initialize the updater with database connection from environment variables"""
        self.db_params = {
            'dbname': os.getenv('POSTGRES_DB', 'miningcore'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        self.token_reader = ReadTokens()
        self.pool_id = 'ErgoSigmanauts'
        self.default_threshold = 0.1  # Default minimum payout if no NFT found
        self.api_base_url = "http://5.78.102.130:8000"
        self.collection_id = "10ba19fae939a8c185eddb239d85f4dc8a77564cb6167578d8019f24696446fc"
        self._db_connection = None

    @property
    def db_connection(self):
        """Lazy database connection"""
        if self._db_connection is None:
            self._db_connection = self.get_db_connection()
        return self._db_connection

    def get_db_connection(self):
        """Create and return a database connection"""
        try:
            return psycopg2.connect(**self.db_params)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def get_all_miners(self) -> List[Dict]:
        """Get all active miners from the API"""
        try:
            url = "http://5.78.102.130:8000/sigscore/miners/bonus"
            params = {
                "limit": 100
            }
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Failed to get miners from API: {response.status_code}")
                return []
                
            miners = response.json()
            logger.info(f"Retrieved {len(miners)} miners from API")
            return miners
        except Exception as e:
            logger.error(f"Error fetching miners: {e}")
            return []

    def verify_nft_ownership(self, token_info: Dict, address: str) -> bool:
        """Verify that the NFT is valid and owned by the miner"""
        try:
            # Check collection ID
            if token_info.get('collection_id') != self.collection_id:
                logger.warning(f"Token has wrong collection ID: {token_info.get('collection_id')}")
                return False
                
            # Verify token type
            if token_info.get('type') != 'Pool Config':
                logger.warning(f"Token has wrong type: {token_info.get('type')}")
                return False
                
            # Verify address ownership
            if token_info.get('address') != address:
                logger.warning(f"Token was minted for different address: {token_info.get('address')}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error verifying NFT ownership: {e}")
            return False

    def get_miner_nft_threshold(self, address: str) -> Optional[float]:
        """Get the minimum payout threshold from a miner's NFT if they have one"""
        try:
            # Create wallet JSON format expected by ReadTokens
            wallet_json = json.dumps({"addresses": [address]})
            
            # Look for Sigma Bytes NFT
            tokens = self.token_reader.find_token_name_in_wallet(wallet_json, 'Sigma BYTES')
            
            if not tokens:
                logger.debug(f"No Sigma Bytes NFT found for address {address}")
                return None
                
            # Check each token found
            for token in tokens:
                token_id = token['tokenId']
                token_info = self.token_reader.get_token_description(token_id)
                
                if not token_info:
                    continue
                    
                # Verify NFT ownership and validity
                if not self.verify_nft_ownership(token_info, address):
                    continue
                    
                # Get minimum payout value
                if 'minimumPayout' in token_info:
                    min_payout = float(token_info['minimumPayout'])
                    logger.info(f"Found valid Sigma Bytes NFT for {address} with minimum payout: {min_payout} ERG")
                    return min_payout
                    
            return None
            
        except Exception as e:
            logger.error(f"Error checking NFT for address {address}: {e}")
            return None

    def update_miner_threshold(self, address: str, new_threshold: float) -> bool:
        """Update a miner's payment threshold in the database"""
        query = """
        UPDATE miner_settings 
        SET paymentthreshold = %s, updated = NOW() 
        WHERE poolid = %s AND address = %s
        """
        
        try:
            with self.db_connection.cursor() as cur:
                cur.execute(query, (new_threshold, self.pool_id, address))
                self.db_connection.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update threshold for {address}: {e}")
            return False

    def get_current_threshold(self, address: str) -> Optional[float]:
        """Get current threshold from database"""
        query = """
        SELECT paymentthreshold 
        FROM miner_settings 
        WHERE poolid = %s AND address = %s
        """
        
        try:
            with self.db_connection.cursor() as cur:
                cur.execute(query, (self.pool_id, address))
                result = cur.fetchone()
                return float(result[0]) if result else None
        except Exception as e:
            logger.error(f"Failed to get current threshold for {address}: {e}")
            return None

    def process_all_miners(self, miners: Optional[List[Dict]] = None):
        """Process all miners and update their payment thresholds based on NFT ownership"""
        if miners is None:
            miners = self.get_all_miners()
            
        logger.info(f"Processing {len(miners)} miners")
        
        for miner in miners:
            address = miner.get('address')
            if not address:
                continue
                
            # Get current threshold from database
            current_threshold = self.get_current_threshold(address)
            if current_threshold is None:
                logger.warning(f"Miner {address} not found in database")
                continue
            
            # Get threshold from NFT
            nft_threshold = self.get_miner_nft_threshold(address)
            
            # Only update if they have a valid NFT and the threshold is different
            if nft_threshold is not None and abs(nft_threshold - current_threshold) > 0.000001:
                logger.info(f"Updating threshold for {address}: {current_threshold} -> {nft_threshold}")
                if self.update_miner_threshold(address, nft_threshold):
                    logger.info(f"Successfully updated threshold for {address}")
                else:
                    logger.error(f"Failed to update threshold for {address}")

    def __del__(self):
        """Close database connection on cleanup"""
        if self._db_connection is not None:
            self._db_connection.close()

def main():
    """Run the payment threshold updater"""
    try:
        updater = PaymentThresholdUpdater()
        
        # Initial run
        logger.info("Starting initial payment threshold update...")
        updater.process_all_miners()
        logger.info("Initial payment threshold update completed.")
        
        # Schedule the next run in 3 hours
        def scheduled_run():
            # Sleep for 3 hours
            time.sleep(3 * 60 * 60)  # 3 hours in seconds
            
            logger.info("Starting scheduled payment threshold update (after 3 hours)...")
            try:
                # Create a new updater instance for the scheduled run
                scheduled_updater = PaymentThresholdUpdater()
                scheduled_updater.process_all_miners()
                logger.info("Scheduled payment threshold update completed.")
            except Exception as e:
                logger.error(f"Error in scheduled run: {e}")
        
        # Start the scheduled run in a separate thread
        scheduler_thread = threading.Thread(target=scheduled_run)
        scheduler_thread.daemon = True  # Thread will exit when main program exits
        scheduler_thread.start()
        
        logger.info("Scheduled next update in 3 hours. Main thread will exit but scheduler will continue.")
        
    except Exception as e:
        logger.error(f"Error running payment threshold updater: {e}")

if __name__ == "__main__":
    main() 