try:
    from utils.api_2_db import DataSyncer
except ModuleNotFoundError:
    from api_2_db import DataSyncer
    
import pandas as pd

def run():
    columns = ['poolId', 'blockHeight', 'networkDifficulty', 'status', 'confirmationProgress', 'effort',
               'transactionConfirmationData', 'reward', 'infoLink', 'hash', 'miner', 'source', 'created']
    db_sync = DataSyncer(config_path="../conf", db_name='localhost')
    
    url = '{}/{}'.format(db_sync.base_api, 'blocks?pageSize=5000')
    block_data = db_sync.get_api_data(url)   

    block_df = pd.DataFrame(block_data, columns=columns)
    block_df.to_csv('block_data.csv')

    print('successfully saved block_data to CSV')
    return

if __name__ == '__main__':
    run()
    
    
