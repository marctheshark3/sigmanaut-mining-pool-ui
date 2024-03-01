from pycoingecko import CoinGeckoAPI
from pandas import DataFrame

def get_prices():
    cg = CoinGeckoAPI()
    prices = cg.get_price(ids=['rosen-bridge', 'ergo', 'spectrum-finance'], vs_currencies='usd')
    df = DataFrame(prices)
    df.to_csv('price_data.csv')

if __name__ == '__main__':
    get_prices()