import random
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SignalGenerator:
    """
    Base class for signal generators.
    """
    def __init__(self):
        """
        Initializes the SignalGenerator.
        """
        logger.debug("SignalGenerator initialized.")
        pass

    def generate_signal(self, historical_data):
        """
        Generates a trading signal based on historical data.

        Args:
            historical_data (pd.DataFrame): A Pandas DataFrame containing historical market data.
                                            Typically requires at least a 'close' column.

        Returns:
            str: A trading signal ("BUY", "SELL", "HOLD").

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        logger.error("generate_signal() called on base SignalGenerator class. Subclasses must implement it.")
        raise NotImplementedError("This method must be implemented by subclasses.")

class RandomSignalGenerator(SignalGenerator):
    """
    Generates a random trading signal.
    """
    def __init__(self):
        super().__init__()
        logger.debug("RandomSignalGenerator initialized.")

    def generate_signal(self, historical_data):
        """
        Generates a random trading signal.

        Args:
            historical_data (pd.DataFrame): Historical market data (not used by this generator).

        Returns:
            str: Randomly chosen "BUY", "SELL", or "HOLD".
        """
        signal = random.choice(["BUY", "SELL", "HOLD"])
        logger.info(f"RandomSignalGenerator generated signal: {signal}")
        return signal

class MovingAverageCrossoverSignalGenerator(SignalGenerator):
    """
    Generates trading signals based on a moving average crossover strategy.
    """
    def __init__(self, short_window=5, long_window=10):
        """
        Initializes the MovingAverageCrossoverSignalGenerator.

        Args:
            short_window (int): The window size for the short moving average.
            long_window (int): The window size for the long moving average.
        """
        super().__init__()
        if short_window >= long_window:
            logger.error(f"Initialization failed for MovingAverageCrossover: short_window ({short_window}) must be less than long_window ({long_window}).")
            raise ValueError("short_window must be less than long_window")
        self.short_window = short_window
        self.long_window = long_window
        logger.debug(f"MovingAverageCrossoverSignalGenerator initialized with short_window={short_window}, long_window={long_window}.")

    def generate_signal(self, historical_data):
        """
        Generates a trading signal based on a moving average crossover.

        Args:
            historical_data (pd.DataFrame): A Pandas DataFrame with a 'close' column.

        Returns:
            str: "BUY" for a bullish crossover, "SELL" for a bearish crossover, "HOLD" otherwise.
        """
        if not isinstance(historical_data, pd.DataFrame):
            logger.warning("Historical data is not a Pandas DataFrame. Returning HOLD.")
            return "HOLD"
        if historical_data is None or historical_data.empty:
            logger.warning("Historical data is None or empty. Returning HOLD.")
            return "HOLD"
        if 'close' not in historical_data.columns:
            logger.warning("'close' column not in historical_data. Returning HOLD.")
            return "HOLD"
        if len(historical_data) < self.long_window:
            logger.warning(f"Not enough data for long_window ({self.long_window}). "
                           f"Data length: {len(historical_data)}. Returning HOLD.")
            return "HOLD"

        try:
            logger.debug(f"Calculating SMAs for {len(historical_data)} data points: short={self.short_window}, long={self.long_window}")
            sma_short = historical_data['close'].rolling(window=self.short_window).mean()
            sma_long = historical_data['close'].rolling(window=self.long_window).mean()
            logger.debug(f"SMA short tail:\n{sma_short.tail(3)}")
            logger.debug(f"SMA long tail:\n{sma_long.tail(3)}")
        except Exception as e:
            logger.error(f"Error calculating SMAs: {e}. Returning HOLD.", exc_info=True)
            return "HOLD"

        if sma_short.isna().sum() >= len(sma_short) -1 or sma_long.isna().sum() >= len(sma_long) -1 :
             logger.warning(f"Not enough non-NaN SMA values to compare. "
                            f"Short window: {self.short_window}, Long window: {self.long_window}, Data length: {len(historical_data)}. Returning HOLD.")
             return "HOLD"

        current_short_sma = sma_short.iloc[-1]
        previous_short_sma = sma_short.iloc[-2]
        current_long_sma = sma_long.iloc[-1]
        previous_long_sma = sma_long.iloc[-2]

        logger.debug(f"Current Short SMA: {current_short_sma}, Previous Short SMA: {previous_short_sma}")
        logger.debug(f"Current Long SMA: {current_long_sma}, Previous Long SMA: {previous_long_sma}")

        if pd.isna(current_short_sma) or pd.isna(previous_short_sma) or \
           pd.isna(current_long_sma) or pd.isna(previous_long_sma):
            logger.warning("NaN values encountered in SMAs needed for crossover detection. Returning HOLD.")
            return "HOLD"

        signal = "HOLD"
        if current_short_sma > current_long_sma and previous_short_sma <= previous_long_sma:
            signal = "BUY"
        elif current_short_sma < current_long_sma and previous_short_sma >= previous_long_sma:
            signal = "SELL"
        
        logger.info(f"MA Crossover Signal generated: {signal} (Short SMA: {current_short_sma:.2f}, Long SMA: {current_long_sma:.2f})")
        return signal

if __name__ == '__main__':
    # Setup basic logging for __main__ execution
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    logger.info("--- Testing Signal Generators ---")

    logger.info("\nTesting RandomSignalGenerator...")
    random_gen = RandomSignalGenerator()
    for _ in range(3): # Reduced loop for brevity
        logger.info(f"Random Signal: {random_gen.generate_signal(None)}") 

    logger.info("\nTesting MovingAverageCrossoverSignalGenerator...")
    data_dict = {
        'timestamp': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                                      '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
                                      '2023-01-11', '2023-01-12', '2023-01-13']),
        'close': [10, 12, 11, 13, 14, 15, 16, 17, 18, 17, 16, 15, 14] 
    }
    sample_df = pd.DataFrame(data_dict)
    
    mavg_gen_3_6 = MovingAverageCrossoverSignalGenerator(short_window=3, long_window=6) 
    logger.info(f"\nUsing short_window=3, long_window=6")

    logger.info("\nTest with insufficient data (first 5 rows):")
    signal_insufficient = mavg_gen_3_6.generate_signal(sample_df.head(5))
    logger.info(f"Signal (insufficient data): {signal_insufficient}") 

    logger.info("\nTest with sufficient data (iterating):")
    for i in range(mavg_gen_3_6.long_window, len(sample_df) + 1):
        current_data = sample_df.iloc[:i]
        signal = mavg_gen_3_6.generate_signal(current_data)
        
        sma_short_val_str = f"{current_data['close'].rolling(window=mavg_gen_3_6.short_window).mean().iloc[-1]:.2f}"
        sma_long_val_str = f"{current_data['close'].rolling(window=mavg_gen_3_6.long_window).mean().iloc[-1]:.2f}"
        
        logger.info(f"Data up to {current_data['timestamp'].iloc[-1].date()}: "
                    f"Close={current_data['close'].iloc[-1]:.2f}, "
                    f"ShortSMA({mavg_gen_3_6.short_window})={sma_short_val_str}, "
                    f"LongSMA({mavg_gen_3_6.long_window})={sma_long_val_str}, "
                    f"Signal: {signal}")
    
    logger.info("\nTest with specific crossover data (Bullish):")
    bullish_data_dict = {
        'close': [20,19,18,17,16, 15, 18, 22, 23]
    }
    bullish_df = pd.DataFrame(bullish_data_dict)
    mavg_bullish_gen = MovingAverageCrossoverSignalGenerator(short_window=3, long_window=5)
    
    for i in range(mavg_bullish_gen.long_window, len(bullish_df) + 1):
        current_data = bullish_df.iloc[:i]
        signal = mavg_bullish_gen.generate_signal(current_data)
        sma_s = current_data['close'].rolling(window=mavg_bullish_gen.short_window).mean()
        sma_l = current_data['close'].rolling(window=mavg_bullish_gen.long_window).mean()
        logger.info(f"Data len {i}: Close={current_data['close'].iloc[-1]}, "
                    f"Prev S={sma_s.iloc[-2]:.2f}, Curr S={sma_s.iloc[-1]:.2f}, "
                    f"Prev L={sma_l.iloc[-2]:.2f}, Curr L={sma_l.iloc[-1]:.2f}, Signal: {signal}")

    logger.info("\nTest with specific crossover data (Bearish):")
    bearish_data_dict = {
        'close': [10,11,12,13,14, 15, 12, 10, 9] 
    }
    bearish_df = pd.DataFrame(bearish_data_dict)
    mavg_bearish_gen = MovingAverageCrossoverSignalGenerator(short_window=3, long_window=5)
    for i in range(mavg_bearish_gen.long_window, len(bearish_df) + 1):
        current_data = bearish_df.iloc[:i]
        signal = mavg_bearish_gen.generate_signal(current_data)
        sma_s = current_data['close'].rolling(window=mavg_bearish_gen.short_window).mean()
        sma_l = current_data['close'].rolling(window=mavg_bearish_gen.long_window).mean()
        logger.info(f"Data len {i}: Close={current_data['close'].iloc[-1]}, "
                    f"Prev S={sma_s.iloc[-2]:.2f}, Curr S={sma_s.iloc[-1]:.2f}, "
                    f"Prev L={sma_l.iloc[-2]:.2f}, Curr L={sma_l.iloc[-1]:.2f}, Signal: {signal}")

    logger.info("\nTest invalid window size (short_window >= long_window):")
    try:
        invalid_gen = MovingAverageCrossoverSignalGenerator(short_window=10, long_window=5)
    except ValueError as e:
        logger.info(f"Caught expected error: {e}")

    logger.info("\nTest missing 'close' column:")
    no_close_df = pd.DataFrame({'open': [1, 2, 3], 'high': [4, 5, 6]})
    signal_no_close = mavg_gen_3_6.generate_signal(no_close_df)
    logger.info(f"Signal (no 'close' column): {signal_no_close}") 

    logger.info("\nTest with None data:")
    signal_none = mavg_gen_3_6.generate_signal(None)
    logger.info(f"Signal (None data): {signal_none}") 

    logger.info("\nTest with non-DataFrame data:")
    signal_list = mavg_gen_3_6.generate_signal([1,2,3,4,5,6,7,8,9,10])
    logger.info(f"Signal (list data): {signal_list}") 

    logger.info("\n--- Testing Complete ---")
