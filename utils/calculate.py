from datetime import datetime
import pytz
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

def calculate_mining_effort(network_difficulty, network_hashrate, hashrate, last_block_timestamp):
    """
    Calculate the mining effort for the pool to find a block on Ergo blockchain based on the given timestamp.
    
    :param network_difficulty: The current difficulty of the Ergo network.
    :param network_hashrate: The total hash rate of the Ergo network (in hashes per second).
    :param hashrate: The hash rate of the miner (in hashes per second).
    :param last_block_timestamp: Timestamp of the last block found in ISO 8601 format.
    :return: The estimated mining effort for the pool.
    """
    network_difficulty = network_difficulty #* 1e15
    network_hashrate = network_hashrate #* 1e12
    hashrate = hashrate #* 1e6
    
    # Parse the last block timestamp
    try:
        last_block_time = datetime.fromisoformat(last_block_timestamp.replace('Z', '+00:00'))
    except (TypeError, ValueError, AttributeError):
        return 0
        
    # Get the current time in UTC
    now = datetime.now(pytz.utc)
    
    # Calculate the time difference in seconds
    time_since_last_block = (now - last_block_time).total_seconds()
    
    # Hashes to find a block at current difficulty
    hashes_to_find_block = network_difficulty  # This is a simplification
    
    # Total hashes by the network in the time since last block
    total_network_hashes = network_hashrate * time_since_last_block
    
    # Pool's share of the total network hashes
    pool_share_of_hashes = (hashrate / network_hashrate) * total_network_hashes
    
    # Effort is the pool's share of hashes divided by the number of hashes to find a block
    effort = pool_share_of_hashes / hashes_to_find_block * 100
    
    return round(effort, 2)

def calculate_time_to_find_block(network_difficulty, network_hashrate, hashrate):
    """
    Calculate the time to find a block on Ergo blockchain.
    
    :param network_difficulty: The current difficulty of the Ergo network.
    :param network_hashrate: The total hash rate of the Ergo network (in hashes per second).
    :param hashrate: The hash rate of the miner (in hashes per second).
    :return: The estimated time to find a block for the miner in days.
    """
    # network_difficulty = network_difficulty * 1e15
    # network_hashrate = network_hashrate * 1e12
    # hashrate = hashrate * 1e6
    
    # Hashes to find a block at current difficulty
    hashes_to_find_block = network_difficulty  # This is a simplification
    
    # Calculate the time to find a block
    try:
        time_to_find_block = hashes_to_find_block / hashrate
    except ZeroDivisionError:
        time_to_find_block = float('inf')
    
    return round(time_to_find_block / 3600 / 24, 2)


def calculate_pplns_participation(shares_data: List[Dict[str, Any]], pool_data: Dict, n_factor: float) -> Tuple[Dict[str, float], float]:
    """
    Calculate the participation percentages for miners based on their current shares.
    
    Args:
        shares_data (List[Dict]): List of dictionaries containing share information per miner.
                                Each dict has 'miner', 'shares', and 'last_share' keys.
        pool_data (Dict): Pool information containing networkdifficulty.
        n_factor (float): Multiplier for PPLNS calculation.
    
    Returns:
        Tuple[Dict[str, float], float]: A tuple containing:
            - Dictionary of miner addresses and their participation percentages
            - Total number of shares considered in the calculation
    """
    try:
        logger.debug(f"Received shares data: {shares_data[:2]}")  # Log first two items for debugging
        
        if not shares_data:
            logger.warning("Empty shares data received")
            return {}, 0

        # Calculate total shares after validating each entry
        total_shares = 0
        valid_shares = []
        
        for miner_data in shares_data:
            try:
                if 'sharespersecond' in miner_data:  # Check if using old key name
                    shares = float(miner_data['sharespersecond'])
                    miner = miner_data['miner']
                elif 'shares' in miner_data:
                    shares = float(miner_data['shares'])
                    miner = miner_data['miner']
                else:
                    logger.warning(f"Missing shares data in entry: {miner_data}")
                    continue
                    
                valid_shares.append((miner, shares))
                total_shares += shares
            except (KeyError, ValueError) as e:
                logger.warning(f"Error processing miner data: {e}, data: {miner_data}")
                continue

        if total_shares == 0:
            logger.warning("No valid shares found in the calculation period")
            return {}, 0

        # Calculate participation percentage for each miner
        participation = {
            miner: shares / total_shares
            for miner, shares in valid_shares
        }

        logger.info(f"PPLNS calculation completed. Total shares: {total_shares}, "
                   f"Number of miners: {len(participation)}")
        
        return participation, total_shares

    except Exception as e:
        logger.error(f"Error calculating PPLNS participation: {e}")
        logger.error(f"Shares data type: {type(shares_data)}")
        if shares_data:
            logger.error(f"First share entry: {shares_data[0] if isinstance(shares_data, list) else 'Not a list'}")
        return {}, 0