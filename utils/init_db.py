try:
    from utils.api_2_db import DataSyncer
except ModuleNotFoundError:
    from api_2_db import DataSyncer
from pandas import Timestamp


def init_db():
    print('intializing DB')
    db_sync = DataSyncer(config_path="../conf")
    # db_sync = db_sync.db.create_database('sigma-db')
    # db_sync.db.delete_db()    
    timenow = Timestamp.now()
    # db_sync.__delete_table__()
    db_sync.__create_table__()
    db_sync.update_pool_stats(timenow)
    # db_sync.db.fetch_data('stats')
    db_sync.update_block_data(timenow)
    # db_sync.db.fetch_data('block')
    db_sync.update_miner_data(timenow)
    print('complete')
    
if __name__ == '__main__':
    init_db()