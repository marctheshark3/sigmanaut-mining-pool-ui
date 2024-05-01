from utils.api_2_db import DataSyncer
from pandas import Timestamp


def update_blocks_and_live_workers():
    db_sync = DataSyncer(config_path="../conf")
    timenow = Timestamp.now()

    # UPDATING BLOCK DATA
    flag = db_sync.update_block_data(timenow)

    # UPDATING LIVE DATA
    db_sync.update_miner_data(timenow, payment=flag, performance=False)

if __name__ == '__main__':
    update_blocks_and_live_workers()