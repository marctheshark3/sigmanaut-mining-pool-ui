from datetime import datetime
import pytz

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


def calculate_pplns_participation(shares_data, block_data, n_factor):
    """
    Calculate the participation percentages for miners in a Pay Per Last N Shares (PPLNS) system.

    This function determines the participation of each miner based on their share contributions
    leading up to a specific block. It uses the network difficulty and a user-defined factor
    to determine how many shares to consider.

    Args:
    shares_data (list): A list of dictionaries containing share information.
                        Each dictionary should have 'blockheight', 'difficulty', and 'miner' keys.
    block_data (list): A list containing a single dictionary with block information.
                       The dictionary should have 'blockheight' and 'networkdifficulty' keys.
    n_factor (float): A multiplier used to determine how many shares to consider relative to 
                      the network difficulty.

    Returns:
    tuple: A tuple containing two elements:
           1. A dictionary of miner addresses and their participation percentages.
           2. The total number of shares considered in the calculation.

    """
    # Sort shares by blockheight in descending order
    shares_data.sort(key=lambda x: x['blockheight'], reverse=True)

    # Get block information
    block_height = block_data['blockheight']
    network_difficulty = block_data['networkdifficulty']
    
    # Calculate the target number of shares based on network difficulty and n_factor
    target_shares = network_difficulty * n_factor

    # Initialize variables
    total_shares = 0
    valid_shares = []
    miner_shares = {}

    # Collect shares until we reach or exceed the target
    for share in shares_data:
        # Skip shares from future blocks
        if share['blockheight'] > block_height:
            continue

        valid_shares.append(share)
        total_shares += share['difficulty']

        # Add share difficulty to miner's total
        miner = share['miner']
        if miner not in miner_shares:
            miner_shares[miner] = 0
        miner_shares[miner] += share['difficulty']

        # Check if we've reached or exceeded the target number of shares
        if total_shares >= target_shares:
            print(share, 'share')
            break

    # Calculate participation percentages for each miner
    participation = {miner: shares / total_shares for miner, shares in miner_shares.items()}

    return participation, total_shares