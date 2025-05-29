import argparse
import os
import sys # For sys.exit

# Assuming the script is run from the project root, add src to Python path
# This might be needed if you run `python main.py` instead of `python -m main`
# However, for module imports like `from src.config_manager import load_config`,
# Python usually handles it if `src` is a package (has __init__.py) and 
# the current working directory is the project root.
# Let's ensure it works robustly.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import logging
from src.config_manager import load_config
from src.logger_setup import setup_logger
from src.exchange_handler import ExchangeHandler
from src.data_fetcher import DataFetcher
from src.models.signal_generator import RandomSignalGenerator, MovingAverageCrossoverSignalGenerator
from src.trading_engine import TradingEngine

CONFIG_FILE_PATH = 'config/config.ini'
CONFIG_EXAMPLE_PATH = 'config/config.example.ini'

# Load config to get log settings early
loaded_config = load_config(CONFIG_FILE_PATH) # Try loading user config first
if not loaded_config: # If user config fails or doesn't exist
    loaded_config = load_config() # Load with defaults from config_manager

log_level = loaded_config.get('LOG_LEVEL', 'INFO')
log_file = loaded_config.get('LOG_FILE', 'logs/app.log')
setup_logger(log_level, log_file)

logger = logging.getLogger(__name__) # For main.py specific logs

def check_config():
    """Checks if config.ini exists and guides the user if not."""
    if not os.path.exists(CONFIG_FILE_PATH):
        logger.error(f"Configuration file '{CONFIG_FILE_PATH}' not found.")
        logger.info(f"Please create it by copying '{CONFIG_EXAMPLE_PATH}' to '{CONFIG_FILE_PATH}' "
                    "and filling in your API credentials and settings.")
        return False
    return True

def handle_get_balance(args):
    logger.info("Handling get-balance command...")
    if not check_config():
        return

    # Config already loaded globally for logger setup, can re-use or load fresh for handler
    config = load_config(CONFIG_FILE_PATH) # Load fresh to ensure it's specific to this operation
    if not config:
        logger.error("Failed to load configuration. Please check its format and content.")
        return

    try:
        handler = ExchangeHandler(
            exchange_id=config['default_exchange_id'],
            api_key=config['api_key'],
            api_secret=config['api_secret'],
            is_testnet=config['use_testnet']
        )
        if not handler.exchange: # Initialization failed
            logger.error("Exchange handler initialization failed. Check exchange ID and credentials.")
            return

        if not handler.load_markets():
            logger.warning("Failed to load markets. Check network or exchange status.")
            return

        balance = handler.fetch_balance()
        if balance:
            logger.info("\n--- Account Balance ---")
            # Iterate through currencies with non-zero balances (or all if you prefer)
            for currency, amount in balance['total'].items():
                if amount > 0: # Or some other threshold if you want to see all
                    logger.info(f"{currency}: {amount}")
            # logger.debug(json.dumps(balance, indent=2)) # For full details
        else:
            logger.error("Could not retrieve balance. Check API permissions or exchange status.")

    except Exception as e:
        logger.error(f"An error occurred while fetching balance: {e}", exc_info=True)

def handle_fetch_ohlcv(args):
    logger.info(f"Handling fetch-ohlcv command for {args.symbol}...")
    if not check_config():
        return

    config = load_config(CONFIG_FILE_PATH)
    if not config:
        logger.error("Failed to load configuration.")
        return

    try:
        handler = ExchangeHandler(
            exchange_id=config['default_exchange_id'],
            api_key=config['api_key'],
            api_secret=config['api_secret'],
            is_testnet=config['use_testnet']
        )
        if not handler.exchange:
            logger.error("Exchange handler initialization failed.")
            return
        if not handler.load_markets(): # Important before fetching data for specific symbols
            logger.warning("Failed to load markets.")
            return

        fetcher = DataFetcher(exchange_handler=handler)
        df = fetcher.fetch_historical_ohlcv(
            symbol=args.symbol,
            timeframe=args.timeframe,
            limit=args.limit,
            output_dir=args.output
        )

        if df is not None:
            if not df.empty:
                logger.info(f"Successfully fetched and saved data for {args.symbol} to {args.output}/ directory.")
                logger.info(f"Shape of data: {df.shape}")
            else:
                logger.info(f"No data returned for {args.symbol} with timeframe {args.timeframe}. An empty CSV might have been created.")
        else:
            logger.error(f"Failed to fetch OHLCV data for {args.symbol}.")

    except Exception as e:
        logger.error(f"An error occurred during fetch-ohlcv: {e}", exc_info=True)

def handle_get_signal(args):
    logger.info(f"Handling get-signal for {args.symbol} using model {args.model}...")
    if not check_config():
        return

    config = load_config(CONFIG_FILE_PATH)
    if not config:
        logger.error("Failed to load configuration.")
        return

    try:
        handler = ExchangeHandler(
            exchange_id=config['default_exchange_id'],
            api_key=config['api_key'],
            api_secret=config['api_secret'],
            is_testnet=config['use_testnet']
        )
        if not handler.exchange:
            logger.error("Exchange handler initialization failed.")
            return
        if not handler.load_markets():
            logger.warning("Failed to load markets.")
            return

        fetcher = DataFetcher(exchange_handler=handler)

        data_limit = args.long_window * 2 if args.model == 'ma_crossover' else 50
        if args.model == 'ma_crossover' and data_limit < args.long_window + 1:
             data_limit = args.long_window + 10 

        logger.info(f"Fetching {data_limit} candles of '1h' data for {args.symbol} to generate signal...")
        historical_data_df = fetcher.fetch_historical_ohlcv(
            symbol=args.symbol,
            timeframe='1h', 
            limit=data_limit,
            output_dir=None 
        )

        if historical_data_df is None or historical_data_df.empty:
            logger.warning(f"Could not fetch sufficient historical data for {args.symbol} to generate a signal.")
            return

        signal_generator = None
        if args.model == 'random':
            signal_generator = RandomSignalGenerator()
        elif args.model == 'ma_crossover':
            if args.short_window >= args.long_window:
                logger.error("For ma_crossover, short_window must be less than long_window.")
                return
            signal_generator = MovingAverageCrossoverSignalGenerator(
                short_window=args.short_window,
                long_window=args.long_window
            )
        else:
            logger.error(f"Unknown model '{args.model}'. This should not happen due to argparse choices.")
            return

        signal = signal_generator.generate_signal(historical_data_df)
        logger.info(f"\n--- Generated Signal for {args.symbol} ({args.model}) ---")
        logger.info(f"Signal: {signal}")
        if args.model == 'ma_crossover':
             logger.info(f"Parameters: Short Window={args.short_window}, Long Window={args.long_window}")


    except Exception as e:
        logger.error(f"An error occurred during get-signal: {e}", exc_info=True)


def handle_execute_trade(args):
    logger.info(f"Handling execute-trade for {args.symbol}, signal {args.signal}, quantity {args.quantity}...")
    if not check_config():
        return

    config = load_config(CONFIG_FILE_PATH)
    if not config:
        logger.error("Failed to load configuration.")
        return

    try:
        handler = ExchangeHandler(
            exchange_id=config['default_exchange_id'],
            api_key=config['api_key'],
            api_secret=config['api_secret'],
            is_testnet=config['use_testnet']
        )
        if not handler.exchange:
            logger.error("Exchange handler initialization failed.")
            return
        
        if not handler.load_markets():
            logger.warning("Failed to load markets. This might affect trade execution if symbol is not recognized.")

        engine = TradingEngine(exchange_handler=handler, config=config) 
        
        logger.info(f"Executing {args.signal} for {args.quantity} of {args.symbol}")
        result = engine.execute_trade(
            symbol=args.symbol,
            signal=args.signal.upper(), 
            quantity=args.quantity
        )

        if result:
            logger.info("\n--- Trade Execution Result ---")
            logger.info(f"Order ID: {result.get('id')}")
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Symbol: {result.get('symbol')}")
            logger.info(f"Side: {result.get('side')}")
            logger.info(f"Amount: {result.get('amount')}")
            # logger.debug(json.dumps(result, indent=2)) # For full details
        else:
            logger.warning("Trade execution did not return a result or failed. Check previous logs.")

    except Exception as e:
        logger.error(f"An error occurred during execute-trade: {e}", exc_info=True)


def main():
    logger.info("Application started.")
    parser = argparse.ArgumentParser(description="Crypto Trading Bot CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # Get Balance command
    parser_balance = subparsers.add_parser('get-balance', help='Fetch and display account balance.')
    parser_balance.set_defaults(func=handle_get_balance)

    # Fetch OHLCV command
    parser_ohlcv = subparsers.add_parser('fetch-ohlcv', help='Fetch historical OHLCV data and save to CSV.')
    parser_ohlcv.add_argument('symbol', type=str, help="Trading symbol (e.g., 'BTC/USDT')")
    parser_ohlcv.add_argument('--timeframe', type=str, default='1h', help="Timeframe (e.g., '1m', '5m', '1h', '1d'). Default: '1h'")
    parser_ohlcv.add_argument('--limit', type=int, default=100, help="Number of candles to fetch. Default: 100")
    parser_ohlcv.add_argument('--output', type=str, default='data', help="Output directory for CSV file. Default: 'data'")
    parser_ohlcv.set_defaults(func=handle_fetch_ohlcv)

    # Get Signal command
    parser_signal = subparsers.add_parser('get-signal', help='Generate a trading signal for a symbol.')
    parser_signal.add_argument('symbol', type=str, help="Trading symbol (e.g., 'BTC/USDT')")
    parser_signal.add_argument('--model', type=str, default='ma_crossover', choices=['random', 'ma_crossover'],
                               help="Signal generation model. Default: 'ma_crossover'")
    parser_signal.add_argument('--short_window', type=int, default=5,
                               help="Short window for MA crossover. Default: 5")
    parser_signal.add_argument('--long_window', type=int, default=10,
                               help="Long window for MA crossover. Default: 10")
    parser_signal.set_defaults(func=handle_get_signal)

    # Execute Trade command
    parser_trade = subparsers.add_parser('execute-trade', help='Execute a trade.')
    parser_trade.add_argument('symbol', type=str, help="Trading symbol (e.g., 'BTC/USDT')")
    parser_trade.add_argument('signal', type=str, choices=['BUY', 'SELL', 'HOLD'],
                              help="Trading signal: BUY, SELL, or HOLD.")
    parser_trade.add_argument('quantity', type=float, help="Quantity of the asset to trade.")
    parser_trade.set_defaults(func=handle_execute_trade)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
