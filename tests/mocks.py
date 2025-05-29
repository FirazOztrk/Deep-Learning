class MockCCXTExchange:
    def __init__(self, exchange_id='mock_exchange', api_key=None, secret=None):
        self.id = exchange_id
        self.apiKey = api_key
        self.secret = secret
        self.markets = {} # Initialize markets attribute

    def fetch_balance(self):
        return {'free': {'USDT': 1000}, 'total': {'USDT': 1000}}

    def load_markets(self): # Add this method
        self.markets = {
            'BTC/USDT': {'symbol': 'BTC/USDT', 'future': False, 'active': True},
            'ETH/USDT:USDT': {'symbol': 'ETH/USDT:USDT', 'future': True, 'active': True},
            'ADA/USDT:USDT': {'symbol': 'ADA/USDT:USDT', 'future': True, 'active': False}, # Inactive future
        }
        return self.markets

    def fetch_ohlcv(self, symbol, timeframe='1h', since=None, limit=1):
        # Return a structure similar to CCXT's OHLCV
        return [[1672531200000, 16000, 16100, 15900, 16050, 100]] # [timestamp, O, H, L, C, V]

class MockExchangeHandler:
    def __init__(self, exchange_id='mock_exchange', api_key='mock_key', api_secret='mock_secret', is_testnet=False):
        self.exchange = MockCCXTExchange(exchange_id, api_key, api_secret)
        # Ensure load_markets is called if your ExchangeHandler's __init__ does it
        # or if methods relying on markets being loaded are called.
        # For simplicity, we can assume it's called or methods call it.

    def fetch_balance(self):
        return self.exchange.fetch_balance()

    def load_markets(self): # Add this method
        return self.exchange.load_markets()

    def fetch_futures_trading_pairs(self):
        self.load_markets() # Ensure markets are loaded
        return [
            market['symbol'] for market in self.exchange.markets.values()
            if market.get('future') and market.get('active')
        ]
