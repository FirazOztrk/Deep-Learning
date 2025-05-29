import pandas as pd
import os
import ccxt # For ccxt.base.errors
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, exchange_handler):
        """
        Initializes the DataFetcher with an ExchangeHandler instance.

        Args:
            exchange_handler (ExchangeHandler): An instance of the ExchangeHandler class.
        """
        self.exchange_handler = exchange_handler
        logger.debug("DataFetcher initialized.")

    def _make_safe_filename(self, symbol):
        """
        Replaces characters in a symbol that are invalid for filenames.
        """
        safe_name = "".join(c if c.isalnum() else "_" for c in symbol)
        logger.debug(f"Original symbol '{symbol}' sanitized to '{safe_name}'.")
        return safe_name

    def fetch_historical_ohlcv(self, symbol, timeframe='1h', since=None, limit=100, output_dir='data'):
        """
        Fetches historical OHLCV data, converts it to a Pandas DataFrame, and saves it to a CSV file.

        Args:
            symbol (str): The trading symbol (e.g., 'BTC/USDT').
            timeframe (str): The timeframe for OHLCV data (e.g., '1h', '1d').
            since (int, optional): Timestamp in milliseconds for the start of the data. Defaults to None.
            limit (int): The maximum number of candles to fetch. Defaults to 100.
            output_dir (str): The directory to save the CSV file. Defaults to 'data'.
                              If None, data is not saved to CSV.

        Returns:
            pd.DataFrame: The OHLCV data as a Pandas DataFrame, or None if an error occurs.
        """
        if not self.exchange_handler or not self.exchange_handler.exchange:
            logger.error("ExchangeHandler not properly initialized in DataFetcher.")
            return None

        logger.info(f"Fetching OHLCV for {symbol}, timeframe {timeframe}, limit {limit}, since {since}.")
        try:
            ohlcv = self.exchange_handler.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            if not ohlcv:
                logger.info(f"No data returned by exchange for {symbol} on timeframe {timeframe}.")
                return pd.DataFrame()

        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching OHLCV for {symbol}: {e}", exc_info=True)
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching OHLCV for {symbol}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching OHLCV for {symbol}: {e}", exc_info=True)
            return None

        logger.debug(f"Fetched {len(ohlcv)} candles for {symbol}.")
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            logger.debug(f"Converted timestamp to datetime. Head of DataFrame:\n{df.head()}")
        else:
            logger.info(f"No data available for {symbol} with timeframe {timeframe}. Returning empty DataFrame.")
            return df # Already an empty DataFrame if ohlcv was empty and processed

        if output_dir is None:
            logger.info("output_dir is None, skipping CSV saving.")
            return df

        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"Ensured output directory '{output_dir}' exists.")
        except OSError as e:
            logger.error(f"Error creating directory {output_dir}: {e}", exc_info=True)
            return None # Or return df without saving if preferred

        exchange_id = self.exchange_handler.exchange.id
        safe_symbol = self._make_safe_filename(symbol)
        filename = f"{exchange_id}_{safe_symbol}_{timeframe}.csv"
        filepath = os.path.join(output_dir, filename)
        logger.debug(f"Constructed filepath: {filepath}")

        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Successfully saved data for {symbol} to {filepath}")
        except IOError as e:
            logger.error(f"Error saving DataFrame to CSV file {filepath}: {e}", exc_info=True)
            return None # Or return df if saving is not critical

        return df

if __name__ == '__main__':
    # Setup basic logging for __main__ execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    logger.info("DataFetcher module loaded for __main__ testing.")
    logger.info("Example (requires config/config.ini with valid credentials and a running exchange like Binance for real data).")

    # Dummy ExchangeHandler for basic testing of file naming and structure
    class DummyExchange:
        def __init__(self, exchange_id):
            self.id = exchange_id
            self.markets = {} 

        def fetch_ohlcv(self, symbol, timeframe, since, limit):
            logger.info(f"[DummyExchange] Fetching OHLCV for {symbol}, {timeframe}, {since}, {limit}")
            if symbol == 'BTC/USDT' and timeframe == '1h':
                return [
                    [1672531200000, 60000, 60100, 59900, 60050, 100],
                    [1672534800000, 60050, 60200, 60000, 60150, 150],
                ]
            elif symbol == 'ETH/USDT' and timeframe == '1d':
                 return [
                    [1672531200000, 2000, 2010, 1990, 2005, 500],
                    [1672617600000, 2005, 2020, 2000, 2015, 550],
                ]
            elif symbol == 'EMPTY/SYMBOL':
                return []
            elif symbol == 'NONEXISTENT/SYMBOL':
                raise ccxt.BadSymbol(f"Symbol {symbol} not found in dummy exchange")
            return []

    class DummyExchangeHandler:
        def __init__(self, exchange_id, api_key=None, api_secret=None, is_testnet=False):
            self.exchange_id = exchange_id
            self.exchange = DummyExchange(exchange_id) 

        def load_markets(self):
            logger.info("[DummyExchangeHandler] Markets loaded (simulated).")
            return True

    logger.info("\n--- Simulating DataFetcher ---")
    dummy_handler = DummyExchangeHandler(exchange_id='binance_dummy')
    fetcher = DataFetcher(exchange_handler=dummy_handler)

    logger.info("\nTest 1: Fetching BTC/USDT 1h data...")
    btc_df = fetcher.fetch_historical_ohlcv('BTC/USDT', timeframe='1h', limit=2)
    if btc_df is not None:
        logger.info(f"BTC/USDT Data:\n{btc_df.head()}")

    logger.info("\nTest 2: Fetching ETH/USDT 1d data to data/crypto...")
    eth_df = fetcher.fetch_historical_ohlcv('ETH/USDT', timeframe='1d', limit=2, output_dir='data/crypto')
    if eth_df is not None:
        logger.info(f"ETH/USDT Data:\n{eth_df.head()}")

    logger.info("\nTest 3: Symbol with special characters (BTC/USDT:USDT)...")
    special_symbol_df = fetcher.fetch_historical_ohlcv('BTC/USDT:USDT', timeframe='1h', limit=1)
    if special_symbol_df is not None:
        logger.info(f"Special Symbol Data (BTC/USDT:USDT):\n{special_symbol_df.head()}")

    logger.info("\nTest 4: Non-existent symbol (NONEXISTENT/SYMBOL)...")
    none_df = fetcher.fetch_historical_ohlcv('NONEXISTENT/SYMBOL', timeframe='1h')
    if none_df is None:
        logger.info("Fetching non-existent symbol handled correctly (returned None).")
    else:
        logger.warning(f"Fetching non-existent symbol did not return None. Returned type: {type(none_df)}")

    logger.info("\nTest 5: DataFetcher with no ExchangeHandler...")
    fetcher_no_handler = DataFetcher(exchange_handler=None)
    no_handler_df = fetcher_no_handler.fetch_historical_ohlcv('BTC/USDT', timeframe='1h')
    if no_handler_df is None:
        logger.info("DataFetcher with no handler handled correctly (returned None).")
    
    logger.info("\nTest 6: Fetching data for EMPTY/SYMBOL (returns empty list from exchange)...")
    empty_df = fetcher.fetch_historical_ohlcv('EMPTY/SYMBOL', timeframe='1h')
    if empty_df is not None and empty_df.empty:
        logger.info("Fetching data for EMPTY/SYMBOL handled correctly (returned empty DataFrame).")
    else:
        logger.warning(f"Fetching data for EMPTY/SYMBOL did not return empty DataFrame. Type: {type(empty_df)}")

    logger.info("\nTest 7: Fetching data with output_dir=None (no CSV save)...")
    no_save_df = fetcher.fetch_historical_ohlcv('BTC/USDT', timeframe='1h', limit=2, output_dir=None)
    if no_save_df is not None:
        logger.info(f"BTC/USDT Data (no save):\n{no_save_df.head()}")
        # Verify no file was created (manual check or more complex test)
        expected_no_save_path = "binance_dummy_BTC_USDT_1h.csv" # assuming default dir if it was saved
        if not os.path.exists(expected_no_save_path): # simplified check
             logger.info(f"File {expected_no_save_path} not found, as expected when output_dir is None.")


    logger.info("\n--- Simulation Complete ---")
    logger.info("Check the 'data/' and 'data/crypto/' directories for output CSV files from relevant tests.")
