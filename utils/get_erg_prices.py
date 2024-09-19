from pycoingecko import CoinGeckoAPI
from pandas import DataFrame

def get_prices():
    cg = CoinGeckoAPI()
    prices = cg.get_price(ids=['rosen-bridge', 'ergo', 'spectrum-finance'], vs_currencies='usd')
    df = DataFrame(prices)
    df.to_csv('price_data.csv')
    
class PriceReader:
    def __init__(self):
        self.cg = CoinGeckoAPI()
        
    def get(self, debug=False):
        # Fetch current price of Bitcoin (BTC) and Ergo (ERG) in USD
        if debug:
            return 10, 10
        else:
            prices = self.cg.get_price(ids=['bitcoin', 'ergo'], vs_currencies='usd')
            btc_price = prices['bitcoin']['usd']
            erg_price = prices['ergo']['usd']
            return btc_price, erg_price
if __name__ == '__main__':
    get_prices()