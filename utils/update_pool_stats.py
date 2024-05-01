from utils.api_2_db import DataSyncer
from pandas import Timestamp

def update_pool_stats():
    db_sync = DataSyncer(config_path="../conf")
    timenow = Timestamp.now()

    # UPDATING POOL STATS
    db_sync.update_pool_stats(timenow)

if __name__ == '__main__':
    update_pool_stats()