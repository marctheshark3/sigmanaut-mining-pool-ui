from utils.api_2_db import DataSyncer
from pandas import Timestamp

def update_payment_and_performance():
    db_sync = DataSyncer(config_path="../conf")
    timenow = Timestamp.now()

    # UPDATING PAYMENT and PERFORMANCE DATA
    db_sync.update_miner_data(timenow, live_data=False)

if __name__ == '__main__':
    update_payment_and_performance()