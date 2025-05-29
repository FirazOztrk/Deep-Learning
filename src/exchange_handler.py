import ccxt
import logging

logger = logging.getLogger(__name__)

class ExchangeHandler:
    def __init__(self, exchange_id, api_key, api_secret, is_testnet=False):
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_testnet = is_testnet

        try:
            self.exchange = getattr(ccxt, self.exchange_id)({
                'apiKey': self.api_key,
                'secret': self.api_secret,
            })

            if self.is_testnet:
                # Attempt to set sandbox mode if supported
                if hasattr(self.exchange, 'set_sandbox_mode'):
                    self.exchange.set_sandbox_mode(True)
                else:
                    logger.warning(f"Sandbox mode is not supported by {self.exchange_id}")

        except ccxt.ExchangeError as e:
            logger.error(f"Error initializing exchange {self.exchange_id}: {e}", exc_info=True)
            self.exchange = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during exchange initialization: {e}", exc_info=True)
            self.exchange = None

    def load_markets(self):
        if not self.exchange:
            logger.error("Exchange not initialized. Cannot load markets.")
            return False
        try:
            logger.info(f"Loading markets for {self.exchange_id}...")
            self.exchange.load_markets()
            logger.info(f"Markets loaded successfully for {self.exchange_id}.")
            return True
        except ccxt.NetworkError as e:
            logger.error(f"Error loading markets for {self.exchange_id} (network issue): {e}", exc_info=True)
            return False
        except ccxt.ExchangeError as e:
            logger.error(f"Error loading markets for {self.exchange_id} (exchange issue): {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading markets for {self.exchange_id}: {e}", exc_info=True)
            return False

    def fetch_balance(self):
        if not self.exchange:
            logger.error("Exchange not initialized. Cannot fetch balance.")
            return None
        try:
            logger.info(f"Fetching balance for {self.exchange_id}...")
            balance = self.exchange.fetch_balance()
            logger.info(f"Balance fetched successfully for {self.exchange_id}.")
            logger.debug(f"Full balance details: {balance}")
            return balance
        except ccxt.NetworkError as e:
            logger.error(f"Error fetching balance for {self.exchange_id} (network issue): {e}", exc_info=True)
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Error fetching balance for {self.exchange_id} (exchange issue): {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching balance for {self.exchange_id}: {e}", exc_info=True)
            return None

    def fetch_futures_trading_pairs(self):
        if not self.exchange:
            logger.error("Exchange not initialized. Cannot fetch futures trading pairs.")
            return None
        if not self.exchange.markets:
            logger.error("Markets not loaded for {self.exchange_id}. Call load_markets() first.")
            return None

        futures_pairs = []
        try:
            logger.info(f"Fetching futures trading pairs for {self.exchange_id}...")
            for symbol, market in self.exchange.markets.items():
                if market.get('future') and market.get('active'):
                    futures_pairs.append(symbol)
            logger.info(f"Found {len(futures_pairs)} active futures trading pairs for {self.exchange_id}.")
            logger.debug(f"Futures pairs: {futures_pairs}")
            return futures_pairs
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching futures trading pairs for {self.exchange_id}: {e}", exc_info=True)
            return None
